// -----------------------------
// Student Signup
// -----------------------------
const studentSignupForm = document.getElementById('studentSignupForm');
if(studentSignupForm){
    studentSignupForm.addEventListener('submit', function(e){
        e.preventDefault(); // prevent default form submit

        const name = document.getElementById('signupName').value;
        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        const center = document.getElementById('signupCenter').value;
        const address = document.getElementById('signupAddress').value;
        const fees = parseFloat(document.getElementById('signupFees').value);

        fetch('https://acceptable-solace-production-06f3.up.railway.app/student_signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password, center, address, fees })
        })
        .then(res => res.json())
        .then(data => alert(data.message))
        .catch(err => console.error(err));
    });
}

// -----------------------------
// Student Login
// -----------------------------
const studentLoginForm = document.getElementById('studentLoginForm');
if(studentLoginForm){
    studentLoginForm.addEventListener('submit', function(e){
        e.preventDefault();

        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;

        fetch('https://acceptable-solace-production-06f3.up.railway.app/student_login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        })
        .then(res => res.json())
        .then(data => {
            if(data.student){
                alert('Login Successful! Welcome ' + data.student.name);
                window.location.href = 'student_dashboard.html';
            } else {
                alert(data.message);
            }
        })
        .catch(err => console.error(err));
    });
}

// -----------------------------
// Admin Login (Fixed & Updated)
// -----------------------------
const adminLoginForm = document.getElementById('adminLoginForm');
if(adminLoginForm){
    adminLoginForm.addEventListener('submit', function(e){
        e.preventDefault();

        const username = document.getElementById('adminUsername').value.trim();
        const password = document.getElementById('adminPassword').value.trim();
        const message = document.getElementById('message');

        if(username === "" || password === ""){
            message.style.color = "red";
            message.innerText = "❌ Fill all fields";
            return;
        }

        fetch('https://acceptable-solace-production-06f3.up.railway.app/admin_login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        })
        .then(res => res.json())
        .then(data => {
            if(data.admin){ 
                message.style.color = "green";
                message.innerText = "✅ Login Successful";
                localStorage.setItem("adminName", data.admin.username || "Admin");
                setTimeout(()=>{ window.location.href="admin.html"; }, 500);
            } else {
                message.style.color = "red";
                message.innerText = "❌ " + (data.message || "Login failed!");
            }
        })
        .catch(err => {
            console.error(err);
            message.style.color = "red";
            message.innerText = "❌ Server error, try again!";
        });
    });
}

// -----------------------------
// Get Students (for admin dashboard)
// -----------------------------
function loadStudents(){
    fetch('https://acceptable-solace-production-06f3.up.railway.app/get_students')
    .then(res => res.json())
    .then(students => {
        const tableBody = document.getElementById('studentsTableBody');
        if(tableBody){
            tableBody.innerHTML = '';
            students.forEach(s => {
                tableBody.innerHTML += `<tr>
                    <td>${s.id}</td>
                    <td>${s.name}</td>
                    <td>${s.email}</td>
                    <td>${s.center}</td>
                    <td>${s.address}</td>
                    <td>${s.fees}</td>
                </tr>`;
            });
        }
    })
    .catch(err => console.error(err));
}

// Call loadStudents() safely on admin dashboard page load
document.addEventListener('DOMContentLoaded', loadStudents);