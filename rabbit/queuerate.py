from functools import wraps, partial

from kombu import Queue, Connection
from kombu.pools import producers
from kombu.log import get_logger
from kombu.common import send_reply

from rpc import conn_dict
from rabbit.exchange import exchange as default_exchange

logger = get_logger(__name__)

class Queuerator(object):

    """Manage Queue and callbacks for a set of Consumers"""

    queues = {}
    callbacks = {}
    dispatch = {}

    def __init__(self, 
                 legacy=True, 
                 queue=None,
                 prefix='rabbitpy',
                 exchange=default_exchange):
        """Constructor

        :legacy: Boolean flag. If True (default) it should try to emulate hase
        functionality by dispatching calls to a single queue to different
        functions. If False, assume that each method is its own queue.
        :prefix: Prefix for consumer queues. Defaults to 'rabbitpy'.
        :queue: Default name for queue
        :exchange: Exchange to use. 
        """
        self._exchange = exchange
        self._prefix = prefix
        self._legacy = legacy
        if legacy:
            if queue is None:
                raise Exception("'queue' is required for legacy implementation.")

        self._queue = queue


    def _error(self, error, message):
        """Return an error if caller sent an unknown command.

        :error: Error data
        :message: Message object

        """
        message.ack()
        self.respond_to_client(message, error)


    def _hase_dispatch(self, body, message):
        """Dispatch function calls to wrapped methods

        :body: data for command. Note: this must contain  a key 'command'
        which dispatch which callback will be called.
        :returns: the data returned by the callback.
        """
        try:
            command = body['command']
            data = body['data']
            callback = self.dispatch[command]
            logger.debug("Calling {!r} with {!r}".format(command, data))
        except KeyError as ke:
            error_message = "Malformed request: {!r}".format(ke)
            logger.error(error_message)
            error = {"error": error_message, "sent": body}
            self._error(error, message)
        except Exception as e:
            error_message = "Unable call method: {!r}".format(e)
            logger.error(error_message)
            error = {"error": error_message, "sent": body}
            self._error(error, message)
        else:
            return callback(data, message)
        

    def _wrap_function(self, function, callback, queue_name):
        """Set up queue used in decorated function.

        :func: wrapped function
        :exchange: exchange to use
        :queue_name: name of queue
        :returns: wrapped function

        """
        name = function.__name__.lower()
        if name not in self.queues:
            self.queues[name] = []
        if name not in self.callbacks:
            self.callbacks[name] = []
        if self._legacy:
            self.dispatch[name] = callback
            self.callbacks[name].append(self._hase_dispatch)
            # Set queue_name to whatever class was instantiated with.
            queue_name = self._queue
        else:
            self.callbacks[name].append(callback)

        # If not set by instance, make same as function name.
        if queue_name is None:
            queue_name = '.'.join([self._prefix, name])            

        routing_key = queue_name
        # Create the queue.
        queue = Queue(queue_name,
                      self._exchange,
                      durable=False,
                      routing_key=routing_key)

        self.queues[name].append(queue)
        # The function returned by the decorator don't really do anything. The process_msg
        # callback added to the consumer is what actually responds to messages
        # from the client on this particular queue.

        def decorate(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                pass
            return wrapper
        return decorate


    def task(self, func=None, *, queue_name=None):
        """Wrap around a function that should be a task.
        The client should not expect anything to be returned.

        """
        if func is None:
            return partial(self.task, queue_name=queue_name)

        def process_message(body, message):
            logger.info("Processing function {!r} with data {!r}".format(func.__name__,
                                                                         body))
            func(body)
            message.ack()

        return self._wrap_function(func, process_message, queue_name)



    def rpc(self, func=None, *, queue_name=None):
        """Wrap around function. This method is modelled after standard RPC
        behaviour where the message sends a reply_to queue and a
        correlation_id back to the client.

        :func: wrap with new standard rpc behaviour
        :queue_name: defaults to "rabbitpy.<func.__name__>"

        """
        if func is None:
            return partial(self.rpc, queue_name=queue_name)

        def process_message(body, message):
            logger.info("Processing function {!r} with data {!r}".format(func.__name__,
                                                                         body))
            response = func(body)
            logger.info("Received response {!r}".format(response))
            self.respond_to_client(message, response)
            message.ack()

        return self._wrap_function(func, process_message, queue_name)


    def respond_to_client(self, message, response={}):
        """Send RPC response back to client.

        :response: datastructure that needs to go back to client.
        """
        with Connection(**conn_dict) as conn:
            with producers[conn].acquire(block=True) as producer:
                # Assume reply_to and correlation_id in message.
                try:
                    send_reply(
                        self._exchange,
                        message,
                        response,
                        producer
                    )
                except KeyError as e:
                    logger.error('Missing key in request {!r}'.format(e))
                except Exception as ex:
                    logger.error('Unable to reply to request {!r}'.format(ex))
                else:
                    logger.info('Reself.connectionplied with response {!r}'.format(response))