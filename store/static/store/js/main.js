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

    // ❌ COD → no box
    if (radio.value === "cod") return;

    // ✅ Show selected payment box
    if (boxes[radio.value]) {
      boxes[radio.value].style.display = "block";
    }
  });
});

// Show default selected payment box
const checked = document.querySelector('input[name="payment"]:checked');
if (checked && boxes[checked.value]) {
  boxes[checked.value].style.display = "block";
}





const payBtn = document.getElementById("pay-btn");

if (payBtn) {
  payBtn.addEventListener("click", function () {

    const selected = document.querySelector('input[name="payment"]:checked');

    if (!selected) {
      alert("Please select a payment method");
      return;
    }

    // ✅ COD
    if (selected.value === "cod") {
      document.getElementById("payment-form").submit();
      return;
    }

    // 🔵 RAZORPAY
    const options = {
      key: RAZORPAY_KEY,
      amount: AMOUNT,
      currency: "INR",
      name: "Travel Equipment Store",
      description: "Order Payment",
      order_id: ORDER_ID,

      handler: function (response) {
  fetch("/verify-razorpay-payment/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({
      razorpay_payment_id: response.razorpay_payment_id,
      razorpay_order_id: response.razorpay_order_id,
      razorpay_signature: response.razorpay_signature,
    }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === "success") {
      // ✅ Redirect to actual order
      window.location.href = `/order-success/`;
    } else {
      alert("Payment verification failed");
    }
  });
}

    };

    const rzp = new Razorpay(options);
    rzp.open();
  });
}




  /* ===============================
     LIVE AJAX SEARCH 🔍
  ================================ */

  const input = document.getElementById("searchInput");
  const resultsBox = document.getElementById("searchResults");

  if (input && resultsBox) {

    let timeout = null;

    input.addEventListener("input", function () {
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

    if (!data.results || data.results.length === 0) {
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
  })
  .catch(err => {
    console.error("Search error:", err);
    resultsBox.innerHTML = `<div class="search-empty">Error loading results</div>`;
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


document.addEventListener("DOMContentLoaded", function () {
  const profileBtn = document.querySelector(".profile-btn");
  const profileMenu = document.querySelector(".profile-menu");

  if (!profileBtn || !profileMenu) return;

  // Toggle on profile button click
  profileBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    profileMenu.style.display =
      profileMenu.style.display === "block" ? "none" : "block";
  });

  // Close when clicking outside
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".profile-dropdown")) {
      profileMenu.style.display = "none";
    }
  });
});




const ordersDataEl = document.getElementById("orders-data");
const revenueDataEl = document.getElementById("revenue-data");

if (ordersDataEl && revenueDataEl) {

  const ordersRaw = JSON.parse(ordersDataEl.textContent);
  const revenueRaw = JSON.parse(revenueDataEl.textContent);

  // ---------------- ORDERS PER DAY ----------------
  const ordersLabels = ordersRaw.map(o => {
    const date = new Date(o.day);
    return date.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short"
    });
  });

  const ordersCounts = ordersRaw.map(o => o.count);

  new Chart(document.getElementById("ordersChart"), {
    type: "line",
    data: {
      labels: ordersLabels,
      datasets: [{
        label: "Orders",
        data: ordersCounts,
        borderWidth: 2,
        tension: 0.4,
        fill: false
      }]
    }
  });

  document.querySelectorAll('.rating-value').forEach(el => {
    let rating = parseFloat(el.innerText);

    if (rating < 3) {
        el.style.backgroundColor = "#d32f2f"; // red
    } else if (rating < 4) {
        el.style.backgroundColor = "#fbc02d"; // yellow
    }
});
  // ---------------- REVENUE PER MONTH ----------------
  const revenueLabels = revenueRaw.map(r => {
    const date = new Date(r.month);
    return date.toLocaleDateString("en-IN", {
      month: "short",
      year: "numeric"
    });
  });

  const revenueTotals = revenueRaw.map(r => r.total || 0);

  new Chart(document.getElementById("revenueChart"), {
    type: "bar",
    data: {
      labels: revenueLabels,
      datasets: [{
        label: "Revenue (₹)",
        data: revenueTotals,
        borderWidth: 1
      }]
    }
  });

}




function toggleDrawer() {
    const drawer = document.getElementById("sideDrawer");
    const overlay = document.getElementById("overlay");

    drawer.classList.toggle("active");
    overlay.classList.toggle("active");

    document.body.classList.toggle("no-scroll");
}

function closeDrawer() {
    document.getElementById("sideDrawer").classList.remove("active");
    document.getElementById("overlay").classList.remove("active");

    document.body.classList.remove("no-scroll");
}

function showReviewBox() {
    document.getElementById("review-box").style.display = "block";
}

function submitReview() {
    const review = document.getElementById("review-text").value;
    const rating = document.querySelectorAll(".star.selected").length; // if using stars

    fetch("/submit-review/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            review: review,
            rating: rating,
            product_id: 1   // pass dynamic product id
        })
    })
    .then(res => res.json())
    .then(data => {
        alert("Review submitted!");
        document.getElementById("review-box").style.display = "none";
    });
}

// CSRF helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            if (cookie.trim().startsWith(name + '=')) {
                cookieValue = cookie.split('=')[1];
            }
        }
    }
    return cookieValue;
}

function showReviewBox(id) {

    const box = document.getElementById("review-box-" + id);

    if (!box) {
        console.log("Review box not found for id:", id);
        return;
    }

    if (box.style.display === "none" || box.style.display === "") {
        box.style.display = "block";
    } else {
        box.style.display = "none";
    }

}

















