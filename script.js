const products = [
    { id: 1, name: "Leather Handbag", price: 4500, category: "Handbags", desc: "Premium quality leather handbag." },
    { id: 2, name: "Running Shoes", price: 3200, category: "Shoes", desc: "Lightweight breathable mesh shoes." },
    { id: 3, name: "Non-stick Pan", price: 2800, category: "Kitchenware", desc: "Durable 24cm granite coating pan." },
    { id: 4, name: "Serving Spoons Set", price: 1200, category: "Kitchenware", desc: "Stainless steel 4-piece set." }
];

let cart = [];
let currentProduct = null;

function init() {
    const grid = document.getElementById('product-grid');
    products.forEach(p => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <div style="height:200px; background:#f4f4f4; margin-bottom:10px"></div>
            <h3>${p.name}</h3>
            <p class="price">Ksh ${p.price}</p>
            <button class="cta-btn" onclick="viewProduct(${p.id})">View Item</button>
        `;
        grid.appendChild(card);
    });
}

function showSection(id) {
    document.querySelectorAll('section').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    window.scrollTo(0,0);
}

function viewProduct(id) {
    currentProduct = products.find(p => p.id === id);
    document.getElementById('detail-title').innerText = currentProduct.name;
    document.getElementById('detail-price').innerText = `Ksh ${currentProduct.price}`;
    document.getElementById('detail-desc').innerText = currentProduct.desc;
    showSection('product-page');
}

function addToCart() {
    cart.push(currentProduct);
    updateCartUI();
    showSection('checkout');
}

function updateCartUI() {
    document.getElementById('cart-count').innerText = cart.length;
    const list = document.getElementById('checkout-list');
    list.innerHTML = '';
    let total = 0;
    
    cart.forEach(item => {
        const div = document.createElement('div');
        div.innerHTML = `<span>${item.name}</span> <span>Ksh ${item.price}</span>`;
        list.appendChild(div);
        total += item.price;
    });
    
    document.getElementById('total-price').innerText = total.toLocaleString();
}

init();