import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import { getDatabase, ref, set, child, update, remove } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-database.js";

const firebaseConfig = {
  apiKey: "AIzaSyCvqw-mwB3N0dQoUylv-kw5bBzhvP784Nc",
  authDomain: "beelforge-7af00.firebaseapp.com",
  projectId: "beelforge-7af00",
  storageBucket: "beelforge-7af00.firebasestorage.app",
  messagingSenderId: "866340341421",
  appId: "1:866340341421:web:3981519835d16692b06824",
  measurementId: "G-SK8E9HRQ0W"
};
const app = initializeApp(firebaseConfig);
const db = getDatabase(app);
// document.addEventListener("DOMContentLoaded", function () {
//   document.getElementById("saveProjectBtn").addEventListener("click", function () {
//     const title = document.getElementById("title").value;
//     const description = document.getElementById("description").value;
//     const imageUrl = document.getElementById("imageUrl").value;
//     const githubLink = document.getElementById("githubLink").value;
//     const liveLink = document.getElementById("liveLink").value;

//     const projectCol = document.createElement("div");
//     projectCol.className = "col-md-6 col-lg-4";
//     projectCol.innerHTML = `
//       <div class="card h-100">
//         <img src="${imageUrl}" class="card-img-top" alt="Project Thumbnail">
//         <div class="card-body">r
//           <h5 class="card-title">${title}</h5>
//           <p class="card-text">${description}</p>
//         </div>
//         <div class="card-footer d-flex justify-content-between">
//           <a href="${githubLink}" class="btn btn-outline-primary btn-sm" target="_blank">GitHub</a>
//           <a href="${liveLink}" class="btn btn-outline-success btn-sm" target="_blank">Live Demo</a>
//           <button class="btn btn-outline-danger btn-sm remove-btn">Remove</button>
//         </div>
//       </div>
//     `;

    // projectCol.querySelector(".remove-btn").addEventListener("click", function () {
    //   const confirmRemove = confirm("Are you sure you want to remove this project?");
    //   if (confirmRemove) {
    //     projectCol.remove();
    //   }
    // });

  //   document.getElementById("projectContainer").appendChild(projectCol);
  //   const userId = "someUserId"; 
  //   set(ref(db, 'projects/' + userId + "/" + title), {
  //     title,
  //     description,
  //     imageUrl,
  //     githubLink,
  //     liveLink
  //   });
  //   document.getElementById("projectForm").reset();
  //   const modalEl = document.querySelector("#addProjectModal");
  //   const modal = bootstrap.Modal.getInstance(modalEl);
  //   modal.hide();
  // });
  const landingPage = document.getElementById('landingPage');
  const loginPage = document.getElementById('loginPage');
  const mainPage = document.getElementById('mainPage');

  const loginButtons = document.querySelectorAll('.navLoginBtn');
  const signUpButtons = document.querySelectorAll('.navSignUpBtn');

  function showLogin() {
    landingPage.style.display = 'none';
    mainPage.style.display = 'none';
    loginPage.style.display = 'flex';
  }
  function showLanding() {
    landingPage.style.display = 'block';
    loginPage.style.display = 'none';
    mainPage.style.display = 'none';
  }
  function showMain() {
    landingPage.style.display = 'none';
    loginPage.style.display = 'none';
    mainPage.style.display = 'block';
  }
  loginButtons.forEach(btn => btn.addEventListener('click', showLogin));
  signUpButtons.forEach(btn => btn.addEventListener('click', showLogin));
  const hireMeBtn = document.getElementById('hireMeBtn');
  const offcanvas = document.getElementById('offcanvasExample');
  const offcanvasInstance = bootstrap.Offcanvas.getOrCreateInstance(offcanvas);

  hireMeBtn.addEventListener('click', function () {
    // Close the offcanvas manually
    if (offcanvasInstance) {
      offcanvasInstance.hide();
    }

    // Give it a tiny delay to finish hiding before opening modal
    setTimeout(() => {
      const modal = new bootstrap.Modal(document.getElementById('hireMeModal'));
      modal.show();
    }, 400); // delay allows offcanvas to fully close
  });
