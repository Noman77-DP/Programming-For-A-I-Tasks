print("Assalam-o-Alaikum Noman! Type 'chalo' to exit.")
while True:
    user_input = input("You: ").lower().strip()
    matched = False
    if user_input == "chalo":
        print("Bot: Allah Hafiz, Noman! Take care.")
        break
    if "hello" in user_input or "salam" in user_input:
        print("Bot: Wa-Alaikum-Assalam, Noman! How is your day going?")
        matched = True
    if "who am i" in user_input or "my name" in user_input:
        print("Bot: Your name is Noman, and you are a 20-year-old AI student.")
        matched = True
    if "laiba" in user_input or "teacher" in user_input:
        print("Bot: Madam Laiba is our Programming for AI teacher.")
        matched = True
    if "car" in user_input or "automotive" in user_input:
        print("Bot: I know you love cars! Automotive passion is the best.")
        matched = True
    if "pubg" in user_input or "fortnite" in user_input or "among us" in user_input:
        print("Bot: You love playing PUBG, Fortnite, and Among Us!")
        matched = True
    if "ai" in user_input or "university" in user_input:
        print("Bot: You are studying AI at Dawood University Karachi.")
        matched = True
    if matched == False:
        print("Bot: I don't understand.")