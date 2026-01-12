document.addEventListener("DOMContentLoaded", function () {


  document.addEventListener("click", function (e) {
    const button = e.target.closest(".add-to-cart-btn, .btn-add-detail");
    if (!button) return;

    e.preventDefault();

    const variantId = button.dataset.variantId;
    const multiplier = button.dataset.multiplier || 1;
    if (!variantId) {
      console.error("Missing variant ID");
      return;
    }

    fetch(`/add-to-cart-ajax/?variant_id=${variantId}&qty=${multiplier}`)

      .then(res => res.json())
      .then(data => {
        if (!data.success) return;

        // Update badge
        const badge = document.getElementById("cart-count");
        if (badge) badge.innerText = data.cart_count;

        // Button UI
        button.innerHTML = "✔ Added";
        button.classList.add("added");
        button.disabled = true;
      })
      .catch(err => console.error("AJAX error:", err));
  });



  /* ===============================
     PAYMENT METHOD TOGGLE
  ================================ */

  const radios = document.querySelectorAll('input[name="payment"]');

  const boxes = {
    upi: document.getElementById("upi-box"),
    card: document.getElementById("card-box"),
    netbanking: document.getElementById("netbanking-box")
  };

  function hideAll() {
    Object.values(boxes).forEach(box => {
      if (box) box.style.display = "none";
    });
  }

  radios.forEach(radio => {
    radio.addEventListener("change", () => {
      hideAll();
      if (boxes[radio.value]) {
        boxes[radio.value].style.display = "block";
      }
    });
  });

  const checked = document.querySelector('input[name="payment"]:checked');
  if (checked && boxes[checked.value]) {
    boxes[checked.value].style.display = "block";
  }


  /* ===============================
     LIVE AJAX SEARCH 🔍
  ================================ */

  const input = document.getElementById("searchInput");
  const resultsBox = document.getElementById("searchResults");

  if (input && resultsBox) {

    let timeout = null;

    input.addEventListener("keyup", function () {
      const query = input.value.trim();
      clearTimeout(timeout);

      if (query.length < 2) {
        resultsBox.innerHTML = "";
        resultsBox.style.display = "none";
        return;
      }

      timeout = setTimeout(() => {
        fetch(`/ajax/search/?q=${query}`)
          .then(res => res.json())
          .then(data => {
            resultsBox.innerHTML = "";

            if (data.results.length === 0) {
              resultsBox.innerHTML = `<div class="search-empty">No results found</div>`;
              resultsBox.style.display = "block";
              return;
            }

            data.results.forEach(item => {
              resultsBox.innerHTML += `
              <a href="/product/${item.id}/" class="search-item">
                <img src="${item.image}" alt="">
                <div>
                  <div class="search-name">
                    ${item.name.replace(
                new RegExp(query, "gi"),
                match => `<span style="color:#2563eb">${match}</span>`
              )}
                  </div>
                  <div class="search-price">₹ ${item.price}</div>
                </div>
              </a>
            `;
            });

            resultsBox.style.display = "block";
          });
      }, 300);
    });

    document.addEventListener("click", function (e) {
      if (!e.target.closest(".nav-search-wrapper")) {
        resultsBox.style.display = "none";
      }
    });

  }


});



function toggleCoupons() {
  const box = document.getElementById("couponDropdown");
  box.style.display = box.style.display === "block" ? "none" : "block";
}



function toggleItems(event, id) {
  event.preventDefault();   // stops link navigation
  event.stopPropagation();  // stops card click

  const el = document.getElementById(id);
  if (!el) return;

  el.style.display = el.style.display === "block" ? "none" : "block";
}



setTimeout(function () {
  let alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    alert.classList.remove('show');
    alert.classList.add('fade');
  });
}, 3000);






document.addEventListener("click", function (e) {

    const btn = e.target.closest(".wishlist-btn");
    if (!btn) return;

    e.preventDefault(); // 🚫 stop page jump

    const productId = btn.dataset.productId;

    fetch(`/wishlist/toggle/${productId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
        },
    })
    .then(response => response.json())
    .then(data => {
        btn.innerHTML = data.added ? "❤️" : "🤍";
    });
});

/* CSRF helper */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}






