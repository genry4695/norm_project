'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Button,
  Text,
  Spinner,
  useToast,
  Card,
  CardBody,
  Divider,
  Badge,
} from '@chakra-ui/react';
import { FiSend } from 'react-icons/fi';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

interface Citation {
  source: string;
  text: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const toast = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: inputValue.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: inputValue.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: `msg_${Date.now() + 1}`,
        type: 'assistant',
        content: data.response,
        citations: data.citations,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      toast({
        title: 'Error',
        description: 'Failed to get response. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Box maxW="4xl" mx="auto" h="100%" display="flex" flexDirection="column">
      <Box p={4} borderBottom="1px" borderColor="gray.200">
        <Text fontSize="lg" fontWeight="bold">
          Westeros Legal Assistant
        </Text>
        <Text fontSize="sm" color="gray.500">
          Ask questions about Westeros laws
        </Text>
      </Box>

      <VStack flex={1} overflowY="auto" p={4} spacing={4} align="stretch">
        {messages.length === 0 && (
          <Box textAlign="center" py={8} color="gray.500">
            <Text fontSize="lg" mb={2}>
              Welcome to the Westeros Legal Assistant
            </Text>
            <Text fontSize="sm">
              Ask me anything about Westeros laws, and I'll provide answers with citations.
            </Text>
          </Box>
        )}

        {messages.map((message) => (
          <Box
            key={message.id}
            alignSelf={message.type === 'user' ? 'flex-end' : 'flex-start'}
            maxW="80%"
          >
            <Card
              bg={message.type === 'user' ? 'blue.500' : 'gray.50'}
              color={message.type === 'user' ? 'white' : 'black'}
            >
              <CardBody p={4}>
                <Text mb={2}>{message.content}</Text>
                
                {message.citations && message.citations.length > 0 && (
                  <Box mt={3}>
                    <Divider mb={3} />
                    <Text fontSize="sm" fontWeight="bold" mb={2}>
                      Sources:
                    </Text>
                    <VStack spacing={2} align="stretch">
                      {message.citations.map((citation, index) => (
                        <Box
                          key={index}
                          p={3}
                          bg="white"
                          borderRadius="md"
                          border="1px"
                          borderColor="gray.200"
                        >
                          <Badge colorScheme="blue" variant="subtle" mb={2}>
                            {citation.source}
                          </Badge>
                          <Text fontSize="sm" color="gray.700">
                            {citation.text}
                          </Text>
                        </Box>
                      ))}
                    </VStack>
                  </Box>
                )}
              </CardBody>
            </Card>
          </Box>
        ))}

        {isLoading && (
          <Box alignSelf="flex-start">
            <Card bg="gray.50">
              <CardBody p={4}>
                <HStack>
                  <Spinner size="sm" />
                  <Text fontSize="sm" color="gray.500">
                    Thinking...
                  </Text>
                </HStack>
              </CardBody>
            </Card>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </VStack>

      <Box p={4} borderTop="1px" borderColor="gray.200">
        <HStack>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about Westeros laws..."
            disabled={isLoading}
            size="lg"
          />
          <Button
            onClick={handleSendMessage}
            disabled={isLoading || !inputValue.trim()}
            colorScheme="blue"
            size="lg"
            px={8}
          >
            <FiSend />
          </Button>
        </HStack>
      </Box>
    </Box>
  );
}
