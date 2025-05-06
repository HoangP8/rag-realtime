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
        """
        Connect to RabbitMQ server

        Note: In the current phase, this is a soft connection that won't
        fail the application if RabbitMQ is not available.
        """
        if self.connection and not self.connection.is_closed:
            return

        try:
            # Connect to RabbitMQ with a timeout to avoid hanging
            # Use connect_robust for automatic reconnection
            self.connection = await asyncio.wait_for(
                aio_pika.connect_robust(get_rabbitmq_url()),
                timeout=5.0  # 5 second timeout
            )

            # Create channel
            self.channel = await self.connection.channel()

            # Create exchange
            self.exchange = await self.channel.declare_exchange(
                RabbitMQConfig.EXCHANGE_NAME,
                type=RabbitMQConfig.EXCHANGE_TYPE,
                durable=True
            )

            self.logger.info("Connected to RabbitMQ")
            return True

        except asyncio.TimeoutError:
            self.logger.warning("RabbitMQ connection timed out - continuing without RabbitMQ")
            return False
        except Exception as e:
            self.logger.warning(f"Error connecting to RabbitMQ (continuing without it): {str(e)}")
            return False

    async def close(self):
        """
        Close RabbitMQ connection

        Note: This is a safe close that won't fail if the connection
        was never established or already closed.
        """
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                self.logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            self.logger.warning(f"Error closing RabbitMQ connection: {str(e)}")

    async def publish(self, routing_key: str, message: Dict[str, Any], priority: int = 0):
        """
        Publish a message to RabbitMQ

        Note: In the current phase, this method will not raise exceptions if
        RabbitMQ is unavailable. It will log warnings and continue.

        Args:
            routing_key: Routing key
            message: Message to publish
            priority: Message priority (0-9)

        Returns:
            bool: True if message was published, False otherwise
        """
        # If not connected, try to connect
        if not self.connection or self.connection.is_closed:
            connection_result = await self.connect()
            if not connection_result:
                self.logger.warning(f"Cannot publish message to {routing_key}: RabbitMQ not connected")
                return False

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
            return True

        except Exception as e:
            self.logger.warning(f"Error publishing message to RabbitMQ (continuing without it): {str(e)}")
            return False

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: List[str],
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to messages from RabbitMQ

        Note: In the current phase, this method will not raise exceptions if
        RabbitMQ is unavailable. It will log warnings and continue.

        Args:
            queue_name: Queue name
            routing_keys: List of routing keys to subscribe to
            callback: Callback function to handle messages

        Returns:
            bool: True if subscription was successful, False otherwise
        """
        # If not connected, try to connect
        if not self.connection or self.connection.is_closed:
            connection_result = await self.connect()
            if not connection_result:
                self.logger.warning(f"Cannot subscribe to {queue_name}: RabbitMQ not connected")
                return False

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
            return True

        except Exception as e:
            self.logger.warning(f"Error subscribing to RabbitMQ queue (continuing without it): {str(e)}")
            return False

    async def unsubscribe(self, queue_name: str):
        """
        Unsubscribe from a queue

        Note: In the current phase, this method will not raise exceptions if
        RabbitMQ is unavailable. It will log warnings and continue.

        Args:
            queue_name: Queue name

        Returns:
            bool: True if unsubscription was successful, False otherwise
        """
        if queue_name not in self.consumers:
            return True

        try:
            # Cancel consumer
            await self.channel.basic_cancel(self.consumers[queue_name])

            # Remove consumer
            del self.consumers[queue_name]

            self.logger.info(f"Unsubscribed from {queue_name}")
            return True

        except Exception as e:
            self.logger.warning(f"Error unsubscribing from RabbitMQ queue (continuing without it): {str(e)}")

            # Still remove from our local tracking
            if queue_name in self.consumers:
                del self.consumers[queue_name]

            return False
