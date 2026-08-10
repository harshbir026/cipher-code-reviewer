// Golden dataset: JS vulnerable functions for multi-language parser tests.

function renderComment(userInput) {
    const container = document.getElementById("comments");
    container.innerHTML = userInput;
}

function getUserByEmail(db, email) {
    return db.query(`SELECT * FROM users WHERE email='${email}'`);
}