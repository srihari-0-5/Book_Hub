document.addEventListener('DOMContentLoaded', () => {
    // =========================================================
    // Flash Message Logic
    // =========================================================
    // Automatically hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(flash => {
        setTimeout(() => {
            flash.classList.add('hidden');
        }, 5000);
    });

    // =========================================================
    // Form Toggling Logic for index.html
    // =========================================================
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const showRegisterLink = document.getElementById('showRegisterLink');
    const toggleContainer = document.querySelector('.form-section p'); // The <p> tag containing the toggle link

    if (loginForm && registerForm && showRegisterLink) {
        showRegisterLink.addEventListener('click', (event) => {
            event.preventDefault(); // Prevent the default link behavior
            
            // Hide the login form and show the register form
            loginForm.style.display = 'none';
            registerForm.style.display = 'flex'; // Use 'flex' to match the CSS
            
            // Update the toggle link text
            toggleContainer.innerHTML = `
                Already have an account? 
                <a href="#" id="showLoginLink" class="text-blue-600 hover:underline font-semibold">Log In here</a>
            `;
            
            // Re-select the new link and add an event listener to it
            const showLoginLink = document.getElementById('showLoginLink');
            if (showLoginLink) {
                showLoginLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    // Hide the register form and show the login form
                    registerForm.style.display = 'none';
                    loginForm.style.display = 'flex';
                    
                    // Restore the original toggle link text
                    toggleContainer.innerHTML = `
                        Don't have an account? 
                        <a href="#" id="showRegisterLink" class="text-blue-600 hover:underline font-semibold">Register here</a>
                    `;
                });
            }
        });
    }
    
    // =========================================================
    // Add to Cart Pop-up Logic for books.html
    // =========================================================
    const addToCartButtons = document.querySelectorAll('.book-card a[href*="/add_to_cart/"]');
    
    addToCartButtons.forEach(button => {
        button.addEventListener('click', async (event) => {
            event.preventDefault(); // Prevent the page from reloading

            // Get the URL from the button's href attribute
            const cartUrl = button.getAttribute('href');

            try {
                // Use the fetch API to send the request to the server
                // This updates the cart without reloading the page
                const response = await fetch(cartUrl);
                
                if (response.ok) {
                    // Create and display a pop-up message
                    const popupMessage = document.createElement('div');
                    popupMessage.textContent = 'Item added to cart!';
                    popupMessage.className = 'flash success';
                    document.body.appendChild(popupMessage);

                    // Automatically hide the pop-up after 3 seconds
                    setTimeout(() => {
                        popupMessage.classList.add('hidden');
                        popupMessage.remove(); // Remove the element from the DOM
                    }, 3000);
                } else {
                    // Handle server errors (e.g., if the book is out of stock)
                    console.error('Failed to add item to cart.');
                    const errorMessage = document.createElement('div');
                    errorMessage.textContent = 'Error adding item to cart!';
                    errorMessage.className = 'flash danger';
                    document.body.appendChild(errorMessage);

                    setTimeout(() => {
                        errorMessage.classList.add('hidden');
                        errorMessage.remove();
                    }, 3000);
                }
            } catch (error) {
                console.error('Network error:', error);
            }
        });
    });
});
