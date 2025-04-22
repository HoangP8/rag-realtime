import React, { useState } from "react";
import { View, Text, TextInput, ScrollView, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import CircleButton from "@/components/CircleButton";
export default function Chat() {
  const router = useRouter();
  const [messages, setMessages] = useState<any[]>([
    { text: `Hello I need some help`, sender: "user" },
    { text: `Okay! How can I help you?`, sender: "bot" },
    { text: `How is the weather today`, sender: "user" },
    {
      text: `In March, Hanoi typically experiences warm and humid conditions, with average daytime temperatures around 26.8°C (80.2°F) and nighttime lows near 19.2°C (66.6°F). The relative humidity averages 74%, and rainfall occurs over approximately 13 days, totaling about 18mm (0.71 inches) for the month.`,
      sender: "bot",
    },
  ]);
  const [input, setInput] = useState("");
  const [type, setType] = useState("audio");

  const sendMessage = () => {
    if (!input.trim()) return;

    const userMessage = { text: input, sender: "user" };
    setMessages([...messages, userMessage]);
    setInput("");
    setType("audio");

    // Simulate bot response
    setTimeout(() => {
      const botMessage = { text: `You said "${input}"`, sender: "bot" };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    }, 1000);
  };

  const initAudioChat = () => {
    router.push("/audioChat");
  };
  const textChanged = (text: string) => {
    setInput(text);
    setType(text === "" ? "audio" : "text");
  };
  return (
    <View style={styles.container}>
      <ScrollView style={styles.chatContainer}>
        {messages.map((msg, index) => (
          <View
            key={index}
            style={[
              styles.messageBubble,
              msg.sender === "user" ? styles.userBubble : styles.botBubble,
            ]}
          >
            <Text style={styles.messageText}>{msg.text}</Text>
          </View>
        ))}
      </ScrollView>
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={textChanged}
          placeholder="Type a message..."
          placeholderTextColor="#000"
        />
        <CircleButton
          onPress={type === "text" ? sendMessage : initAudioChat}
          type={type}
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
    backgroundColor: "#ffffff",
  },
  chatContainer: {
    flex: 1,
    marginBottom: 10,
  },
  messageBubble: {
    padding: 10,
    marginVertical: 5,
    borderRadius: 10,
    maxWidth: "80%",
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: "#E3E3E5",
    padding: 12,
    borderRadius: 50,
  },
  botBubble: {
    alignSelf: "flex-start",
    backgroundColor: "#ffffff",
  },
  messageText: {
    color: "#000",
    fontSize: 16,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  input: {
    flex: 1,
    padding: 15,
    backgroundColor: "#fff",
    borderColor: "#134D8B",
    borderWidth: 2,
    borderRadius: 30,
    color: "#000",
  },
});
