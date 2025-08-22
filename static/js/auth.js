// Import Firebase (modular style)
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  updateProfile,
  sendEmailVerification,
  signInWithEmailAndPassword,
  signOut
} from "https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js";
import { sendPasswordResetEmail } from "https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js";

// Your Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyCvqw-mwB3N0dQoUylv-kw5bBzhvP784Nc",
  authDomain: "beelforge-7af00.firebaseapp.com",
  projectId: "beelforge-7af00",
  storageBucket: "beelforge-7af00.appspot.com",
  messagingSenderId: "866340341421",
  appId: "1:866340341421:web:3981519835d16692b06824",
  measurementId: "G-SK8E9HRQ0W"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
function showWelcome(username) {
  document.getElementById("signupPage").style.display = "none";
  const message = `
    <h4>Welcome, ${username}!</h4>
    <p>We’ve sent you a verification email. Please check your inbox.</p>
  `;
  const welcomeEl = document.getElementById("welcomeMessage");
  welcomeEl.innerHTML = message;
  welcomeEl.style.display = "block";
  welcomeEl.style.color = "red";

  setTimeout(() => {
    window.location.href = "login.html";
  }, 10000);
}

// Sign Up
const signupForm = document.getElementById("signupForm");
if (signupForm) {
  signupForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const username = document.getElementById("username").value.trim();

    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      await updateProfile(user, { displayName: username });
      await sendEmailVerification(user);

      showWelcome(username);
      e.target.reset();
    } catch (error) {
      alert("Error: " + error.message);
    }
  });
}

// Login
const loginForm = document.getElementById("loginForm");
if (loginForm) {
  loginForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;

      if (!user.emailVerified) {
        alert("Please verify your email before logging in.");
        await signOut(auth);
      } else {
        console.log("Login success:", user.email);
        window.location.href = "main.html";
      }
    } catch (error) {
      alert("Login error: " + error.message);
    }
  });
  document.getElementById("resetForm").addEventListener("submit", async function (e) {
    e.preventDefault();
    const resetForm = document.getElementById("resetForm");
if (resetForm) {
  resetForm.addEventListener("submit", async function(e) {
    e.preventDefault();
    const email = document.getElementById("resetEmail").value.trim();

    try {
      await sendPasswordResetEmail(auth, email);
      alert("Password reset email sent! Check your inbox.");
    } catch (error) {
      alert("Error: " + error.message);
    }
  });
}
  });
}
