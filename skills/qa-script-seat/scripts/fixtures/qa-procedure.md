# QA procedure — STORY-42: login rejects a wrong password

You are a human. You are operating this system at the UI. You must prove that the system works.

1. Open `/login`. Observe: the email field and the password field are both visible.
2. Type a known email with a wrong password and press **Sign in**. Observe: the message
   "Incorrect email or password" appears and the address bar still reads `/login`.
