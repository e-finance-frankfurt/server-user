# !/usr/bin/env python3
# -*- coding: utf-8 -*-

# general imports
import tensorflow as tf

# specific imports
from itertools import islice

class TensorflowHandler:

    def __init__(self, model=None):
        """
        Use TFHandler with custom generators that do not inherit from 
        tf.keras.utils.Sequence. 
        
        Keep overridden tf.keras.Model.fit, .evaluate and .predict method in a 
        separate class because otherwise, making them part of tf.keras.Model
        itself, (re-)loaded models could use them. 

        :param model:
            tf.keras.Model, model instance, optional at the time of instantiation
        """

        # may also be set later by .load_model method
        self.model = model 

        # ...
        # TODO: infer input shapes required from input generators

    @tf.function
    def _distribute_train_step(self, batch_train):

        # distribute _train_step on batch_train across replicas
        loss_per_replica = self.model.distribute_strategy.run(
            self._train_step, args=(batch_train,))
        
        # reduce loss_per_replica to (total) loss 
        # model weights have already been updated at this point, reduce only to have a scalar loss value!
        loss = self.model.distribute_strategy.reduce(
            tf.distribute.ReduceOp.SUM, loss_per_replica, axis=None)

        return loss

    def _train_step(self, batch_train):

        x_train, y_train = batch_train
        
        # get prediction, compute loss value, record gradient
        with tf.GradientTape() as tape:
            y_pred = self.model(x_train, training=True)
            loss = self.model.compiled_loss(y_train, y_pred) # loss function
        
        # update weights
        grads = tape.gradient(loss, self.model.trainable_weights)
        self.model.optimizer.apply_gradients(zip(grads, self.model.trainable_weights))
        
        # update metrics
        self.model.compiled_metrics.update_state(y_train, y_pred)

        return loss

    def fit(
        self,
        input_train, # type SequenceGenerator
        input_valid, # type SequenceGenerator
        epochs:int=1,
        limit_train:int=None,
        limit_valid:int=None,
        callbacks=None,
    ):
        """
        Fit model over specified number of epochs based on input generator.

        This method has been adjusted to work with custom generators that are
        not required to subclass tf.keras.utils.Sequence.

        :param input_train:
            InputGenerator, generator class instance
        :param input_valid:
            InputGenerator, generator class instance
        :param epochs:
            int, number of epochs
        :param limit_train:
            int/None, maximal number of train steps
        :param limit_valid:
            int/None, maximal number of valid steps
        :param callbacks:
            list, tf.keras.callbacks.Callback instances
        """

        # train_begin callbacks
        print("\nStart training ...")
        if not isinstance(callbacks, tf.keras.callbacks.CallbackList):
            callbacks = tf.keras.callbacks.CallbackList(
                callbacks, model=self.model, verbose=1, steps=1, epochs=epochs,
            )
        self.model.stop_training = False # used by callbacks
        callbacks.on_train_begin()

        for epoch in range(epochs):

            # reset metrics before every epoch
            self.model.reset_metrics()

            # epoch_begin callbacks
            print("\nEpoch {}/{}:".format(epoch+1, epochs))
            callbacks.on_epoch_begin(epoch)

            # train loop definition
            print("Train on {} batches ...".format(limit_train or "?"))
            loop_train = enumerate(islice(input_train, 0, limit_train))
            # train progbar definition
            progbar_train = tf.keras.utils.Progbar(limit_train)

            # train loop iteration
            for step, batch_train in loop_train:
                # ...
                callbacks.on_train_batch_begin(step)
                _ = self._distribute_train_step(batch_train)
                callbacks.on_train_batch_end(step+1)
                progbar_train.add(1, values=self.metrics_state)

            # train_logs are latest train metrics
            train_logs = dict(self.metrics_state)
            # valid_logs are validation metrics
            valid_logs = self.evaluate(input_valid, limit_valid, callbacks)

            # epoch_end callbacks
            callbacks.on_epoch_end(epoch+1, {**train_logs, **valid_logs})
            if self.model.stop_training:
                break

        # train_end callbacks
        callbacks.on_train_end()

        return self.model.history

    @tf.function
    def _distribute_test_step(self, batch_test):

        # distribute _test_step on batch_test across replicas
        loss_per_replica = self.model.distribute_strategy.run(
            self._test_step, args=(batch_test,))
        
        # reduce loss_per_replica to (total) loss 
        # model weights have already been updated at this point, reduce only to return a scalar loss value!
        loss = self.model.distribute_strategy.reduce(
            tf.distribute.ReduceOp.SUM, loss_per_replica, axis=None)

        return loss

    def _test_step(self, batch_test):

        x_test, y_test = batch_test
        # get prediction, compute loss value
        y_pred = self.model(x_test, training=False)
        loss = self.model.compiled_loss(y_test, y_pred) # loss function
        # update metrics
        self.model.compiled_metrics.update_state(y_test, y_pred)

        return loss

    def evaluate(
        self,
        input_test, # type SequenceGenerator
        limit_test:int=None,
        callbacks:list=None,
    ):
        """
        Evaluate model based on input generator.

        :param input_test:
            InputGenerator, generator class instance
        :param limit_test:
            int, maximal number of test steps
        :param callbacks:
            list, tf.keras.callbacks.Callback instances
        """

        # test_begin callbacks
        if not isinstance(callbacks, tf.keras.callbacks.CallbackList):
            callbacks = tf.keras.callbacks.CallbackList(
                callbacks, model=self.model, verbose=1, steps=1, epochs=1,
            )
        callbacks.on_test_begin()

        # reset metrics before evaluation
        self.model.reset_metrics()

        # test loop definition
        print("\nEvaluate on {} batches ...".format(limit_test or "?"))
        loop_test = enumerate(islice(input_test, 0, limit_test))
        # test progbar definition
        progbar_test = tf.keras.utils.Progbar(limit_test)

        # test loop iteration
        for step, batch_test in loop_test:
            # ...
            callbacks.on_test_batch_begin(step)
            _ = self._distribute_test_step(batch_test)
            callbacks.on_test_batch_end(step+1)
            progbar_test.add(1, values=self.metrics_state)

        # test_logs are latest test metrics
        test_logs = {"val_" + attr: value for attr, value in self.metrics_state}

        # test_end callbacks
        callbacks.on_test_end()

        return test_logs

    @tf.function
    def _distribute_pred_step(self, batch_pred):

        # distribute _test_step on batch_test across replicas
        pred_per_replica = self.model.distribute_strategy.run(
            self._pred_step, args=(batch_pred,))
        
        # reduce pred_per_replica to concatenated pred
        # note that reduce_per_replica is not part of the API, may therefore change in future versions
        # https://github.com/tensorflow/tensorflow/blob/a4dfb8d1a71385bd6d122e4f27f86dcebb96712d/tensorflow/python/keras/engine/training.py#L2780-L2809
        pred = tf.python.keras.engine.training.reduce_per_replica(
            pred_per_replica, 
            strategy=self.model.distribute_strategy, 
            reduction="concat",
        )

        return pred

    @property
    def metrics_state(self):
        """
        Computed metrics used to update logs within train and test loop.

        :return metrics:
            list, [(metric_name, metric_value), *] list
        """

        # get metric names and values
        metrics_state = [(m.name, m.result()) for m in self.model.metrics]

        return metrics_state
    
    @property
    def input_shape(self):
        """
        Input shape required by model. 
        
        :return input_shape:
            tuple/None, ...
        """
        
        # available only if model instance is set and has been trained
        try:
            input_shape = self.model.input_shape
        # ...
        except:
            input_shape = None
            
        return input_shape
    
    def load_model(self, path):
        """
        Load pre-trained model. 

        :param path:
            str, ...
        """

        # ...
        self.model = tf.keras.models.load_model(path)
    
    def save_model(self, path):
        """
        Use lower-level API for saving (and loading) subclassed model.

        https://www.tensorflow.org/tutorials/distribute/save_and_load#caveats

        :param path:
            str, ...
        """

        # model.save(path) gives error
        tf.saved_model.save(self.model, path)


class PytorchHandler:

    def __init__(self, model=None):
        pass


