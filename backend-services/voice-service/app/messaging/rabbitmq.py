"""
RabbitMQ message broker for event-driven architecture
"""
import asyncio
import json
import logging
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional

import aio_pika
from aio_pika import ExchangeType, Message

from app.config import settings


class RabbitMQConfig:
    """RabbitMQ configuration"""
    
    # Connection settings
    HOST = settings.RABBITMQ_HOST
    PORT = settings.RABBITMQ_PORT
    USER = settings.RABBITMQ_USER
    PASSWORD = settings.RABBITMQ_PASSWORD
    VHOST = settings.RABBITMQ_VHOST
    
    # Exchange settings
    EXCHANGE_NAME = "medical_chatbot"
    EXCHANGE_TYPE = ExchangeType.TOPIC
    
    # Queue settings
    VOICE_QUEUE = "voice_events"
    CONVERSATION_QUEUE = "conversation_events"
    LLM_QUEUE = "llm_events"


@lru_cache()
def get_rabbitmq_url() -> str:
    """
    Get RabbitMQ connection URL
    
    Returns:
        Connection URL string
    """
    config = RabbitMQConfig
    return f"amqp://{config.USER}:{config.PASSWORD}@{config.HOST}:{config.PORT}/{config.VHOST}"


class RabbitMQService:
    """
    RabbitMQ service for event-driven architecture
    Handles publishing and consuming messages
    """
    
    def __init__(self):
        """Initialize RabbitMQ service"""
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queues = {}
        self.consumers = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect(self):
        """Connect to RabbitMQ server"""
        if self.connection and not self.connection.is_closed:
            return
        
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(get_rabbitmq_url())
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Create exchange
            self.exchange = await self.channel.declare_exchange(
                RabbitMQConfig.EXCHANGE_NAME,
                type=RabbitMQConfig.EXCHANGE_TYPE,
                durable=True
            )
            
            self.logger.info("Connected to RabbitMQ")
        
        except Exception as e:
            self.logger.error(f"Error connecting to RabbitMQ: {str(e)}")
            raise
    
    async def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self.logger.info("Disconnected from RabbitMQ")
    
    async def publish(self, routing_key: str, message: Dict[str, Any], priority: int = 0):
        """
        Publish a message to RabbitMQ
        
        Args:
            routing_key: Routing key
            message: Message to publish
            priority: Message priority (0-9)
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()
        
        try:
            # Convert message to JSON
            message_body = json.dumps(message).encode()
            
            # Create message
            rabbitmq_message = Message(
                body=message_body,
                content_type="application/json",
                priority=priority
            )
            
            # Publish message
            await self.exchange.publish(
                message=rabbitmq_message,
                routing_key=routing_key
            )
            
            self.logger.debug(f"Published message to {routing_key}")
        
        except Exception as e:
            self.logger.error(f"Error publishing message: {str(e)}")
            raise
    
    async def subscribe(
        self, 
        queue_name: str, 
        routing_keys: List[str], 
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to messages from RabbitMQ
        
        Args:
            queue_name: Queue name
            routing_keys: List of routing keys to subscribe to
            callback: Callback function to handle messages
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()
        
        try:
            # Declare queue
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={"x-max-priority": 9}
            )
            
            # Bind queue to exchange with routing keys
            for routing_key in routing_keys:
                await queue.bind(self.exchange, routing_key)
            
            # Store queue
            self.queues[queue_name] = queue
            
            # Create consumer
            async def process_message(message):
                async with message.process():
                    try:
                        # Parse message body
                        message_body = json.loads(message.body.decode())
                        
                        # Call callback
                        await callback(message_body)
                    
                    except Exception as e:
                        self.logger.error(f"Error processing message: {str(e)}")
            
            # Start consuming
            consumer_tag = await queue.consume(process_message)
            self.consumers[queue_name] = consumer_tag
            
            self.logger.info(f"Subscribed to {queue_name} with routing keys {routing_keys}")
        
        except Exception as e:
            self.logger.error(f"Error subscribing to queue: {str(e)}")
            raise
    
    async def unsubscribe(self, queue_name: str):
        """
        Unsubscribe from a queue
        
        Args:
            queue_name: Queue name
        """
        if queue_name not in self.consumers:
            return
        
        try:
            # Cancel consumer
            await self.channel.basic_cancel(self.consumers[queue_name])
            
            # Remove consumer
            del self.consumers[queue_name]
            
            self.logger.info(f"Unsubscribed from {queue_name}")
        
        except Exception as e:
            self.logger.error(f"Error unsubscribing from queue: {str(e)}")
            raise
