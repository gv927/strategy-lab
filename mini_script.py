#!/usr/bin/env python3
"""Mini script — say hello and get a personalized response."""

while True:
    user_input = input("You: ").strip().lower()
    if user_input == "hello":
        print("Bot: Hi Sadam! 😊")
    elif user_input in ("quit", "exit", "bye"):
        print("Bot: Goodbye Sadam! 👋")
        break
    elif user_input:
        print("Bot: Say 'hello' to talk to me!")
