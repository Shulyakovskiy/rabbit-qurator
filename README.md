#rabbitpy

** WORK IN PROGRESS **

A library for creating RPC tools


#Description

This library is intended to support microservices that need to interface with
RabbitMQ.  It provides a couple wrappers that can be used to turn functions
into RPC style endpoints or fire-and-forget tasks.

#Installation


```
pip install rabbitpy  
```

#Usage

##Consumer



```python
from rabbitpy.queurate import Queuerator
consumer = Queuerator(legacy=False, exchange=some_exchange)

@consumer.rpc
def do_something(*args, **kwargs):
    # some logic
    return {"message": "Hello"}

```

##Client

You can implement clients however you like. Here is an example:
```python
from rabbitpy.rpc.client import RpcClient

client = RpcClient(exchange=some_exchange)
client.rpc('do_something', {"msg": "Test"})
for reply in client.retrieve_messages():
    # reply somewhere in here

```


#Synopsis


Create a hase like queue:
```python
from rabbitpy.queuerate import Queuerator

legacy_consumer = Queuerator(queue='api.some.queue')

@legacy_consumer.rpc
def my_rpc_method(data);
    try:
        # do some stuff
        response = do_stuff(data)
        return response
    except Exception as e:
        return {"error": "There was an error! {!r}".format(e)}

```

This expects the client to send something like the following to the queue `api.some.queue`:
```javascript
{
    "command": "my_rpc_method",
    "data": {
        "domain": "something.com"
        ...
    }
}
```


Alternative method for defining queues:

```python
consumer = Queuerator(legacy=False,
                      prefix='awesome')

@consumer.rpc
def my_rpc_method(data);
    try:
        # do some stuff
        response = do_stuff(data)
        return response
    except Exception as e:
        return {"error": "There was an error! {!r}".format(e)}
```

This expects the client to send the following to the `awesome.my_rpc_method` queue:
```javascript
{
    "domain": "something.com",
    ...
}
```

* `prefix` parameter to the constructor defaults to `rabbitpy`.

#General Notes

##Environment

In order to interact with RabbitMQ, you need to be sure that the following
environment variables are set when starting the docker container with
`./launch.sh`:

1. `RABBITMQ_TRANSPORT_SERVICE_HOST`
1. `RABBITMQ_TRANSPORT_SERVICE_PORT`
1. `RABBITMQ_USER`
1. `RABBITMQ_PASS`
1. `RABBITMQ_VHOST`



##Miscellaneous information
* The *hase-like* implementation is on by default.
* When using the *hase-like* implementation, a queue name is required.
* This is a work in progress and subject to unannounced sporadic changes.
