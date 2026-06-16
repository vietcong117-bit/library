// Sample book data
const booksData = [
  {
    id: 1,
    title: 'Clean Code',
    author: 'Robert C. Martin',
    category: 'tech',
    status: 'available',
    image: 'https://picsum.photos/180/240?random=1',
  },
  {
    id: 2,
    title: 'Design Patterns',
    author: 'Gang of Four',
    category: 'tech',
    status: 'borrowed',
    image: 'https://picsum.photos/180/240?random=2',
  },
  {
    id: 3,
    title: 'The Great Gatsby',
    author: 'F. Scott Fitzgerald',
    category: 'fiction',
    status: 'available',
    image: 'https://picsum.photos/180/240?random=3',
  },
  {
    id: 4,
    title: 'Atomic Habits',
    author: 'James Clear',
    category: 'selfhelp',
    status: 'available',
    image: 'https://picsum.photos/180/240?random=4',
  },
  {
    id: 5,
    title: 'Business Model Canvas',
    author: 'Alexander Osterwalder',
    category: 'business',
    status: 'borrowed',
    image: 'https://picsum.photos/180/240?random=5',
  },
  {
    id: 6,
    title: 'The Lean Startup',
    author: 'Eric Ries',
    category: 'business',
    status: 'available',
    image: 'https://picsum.photos/180/240?random=6',
  },
  {
    id: 7,
    title: 'JavaScript: The Good Parts',
    author: 'Douglas Crockford',
    category: 'tech',
    status: 'available',
    image: 'https://picsum.photos/180/240?random=7',
  },
  {
    id: 8,
    title: 'Refactoring',
    author: 'Martin Fowler',
    category: 'tech',
    status: 'available',
    image: 'https://picsum.photos/180/240?random=8',
  },
];

let favorites = [];
let borrowed = [];

document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('themeToggle');
  const menuToggle = document.getElementById('menuToggle');
  const navItems = document.querySelectorAll('.nav-item');
  const searchInput = document.getElementById('searchInput');
  const categoryFilter = document.getElementById('categoryFilter');
  const statusFilter = document.getElementById('statusFilter');
  const sortFilter = document.getElementById('sortFilter');

  // Theme toggle
  themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
  });

  // Load saved theme
  if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
  }

  // Mobile menu
  menuToggle.addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('open');
  });

  // Navigation
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const section = item.getAttribute('data-section');
      showSection(section);
      navItems.forEach(nav => nav.classList.remove('active'));
      item.classList.add('active');
      if (window.innerWidth <= 768) {
        document.querySelector('.sidebar').classList.remove('open');
      }
    });
  });

  // Render books
  renderBooks();
  renderFavorites();
  renderBorrowed();

  // Filter and search
  searchInput.addEventListener('input', renderBooks);
  categoryFilter.addEventListener('change', renderBooks);
  statusFilter.addEventListener('change', renderBooks);
  sortFilter.addEventListener('change', renderBooks);
});

function showSection(section) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(s => s.classList.remove('active'));
  document.getElementById(section + 'Section').classList.add('active');

  const titleMap = {
    dashboard: 'Dashboard',
    books: 'Kho sách',
    favorites: 'Sách yêu thích',
    borrowed: 'Sách đang mượn',
  };
  document.getElementById('sectionTitle').textContent = titleMap[section] || section;
}

function renderBooks() {
  const grid = document.getElementById('booksGrid');
  const search = document.getElementById('searchInput').value.toLowerCase();
  const category = document.getElementById('categoryFilter').value;
  const status = document.getElementById('statusFilter').value;
  const sort = document.getElementById('sortFilter').value;

  let filtered = booksData.filter(book => {
    const matchSearch = book.title.toLowerCase().includes(search) || book.author.toLowerCase().includes(search);
    const matchCategory = !category || book.category === category;
    const matchStatus = !status || book.status === status;
    return matchSearch && matchCategory && matchStatus;
  });

  if (sort === 'title') {
    filtered.sort((a, b) => a.title.localeCompare(b.title));
  }

  grid.innerHTML = filtered.map(book => `
    <div class="book-card">
      <img src="${book.image}" alt="${book.title}" class="book-card-image">
      <div class="book-card-content">
        <p class="book-card-title">${book.title}</p>
        <p class="book-card-author">${book.author}</p>
        <div class="book-card-footer">
          <span class="book-status ${book.status === 'available' ? 'status-available' : 'status-borrowed'}">
            ${book.status === 'available' ? 'Có sẵn' : 'Đang mượn'}
          </span>
          <button class="btn-heart ${favorites.includes(book.id) ? 'liked' : ''}" onclick="toggleFavorite(${book.id})">
            <i class="fas fa-heart"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderFavorites() {
  const grid = document.getElementById('favoritesGrid');
  const favoriteBooks = booksData.filter(b => favorites.includes(b.id));
  grid.innerHTML = favoriteBooks.map(book => `
    <div class="book-card">
      <img src="${book.image}" alt="${book.title}" class="book-card-image">
      <div class="book-card-content">
        <p class="book-card-title">${book.title}</p>
        <p class="book-card-author">${book.author}</p>
        <div class="book-card-footer">
          <span class="book-status ${book.status === 'available' ? 'status-available' : 'status-borrowed'}">
            ${book.status === 'available' ? 'Có sẵn' : 'Đang mượn'}
          </span>
          <button class="btn-heart liked" onclick="toggleFavorite(${book.id})">
            <i class="fas fa-heart"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

function renderBorrowed() {
  const list = document.getElementById('borrowedList');
  const borrowedBooks = booksData.filter(b => b.status === 'borrowed');
  list.innerHTML = borrowedBooks.map(book => `
    <div class="borrowed-item">
      <div class="borrowed-item-info">
        <img src="${book.image}" alt="${book.title}" class="borrowed-item-img">
        <div class="borrowed-item-details">
          <h4>${book.title}</h4>
          <p>Tác giả: ${book.author}</p>
          <p>Mượn từ: ${new Date(Date.now() - 15*24*60*60*1000).toLocaleDateString('vi-VN')}</p>
        </div>
      </div>
      <div class="borrowed-due">
        <p class="due-date">Hạn trả: ${new Date(Date.now() + 5*24*60*60*1000).toLocaleDateString('vi-VN')}</p>
        <button class="btn-return">Trả sách</button>
      </div>
    </div>
  `).join('');
}

function toggleFavorite(bookId) {
  const idx = favorites.indexOf(bookId);
  if (idx > -1) {
    favorites.splice(idx, 1);
  } else {
    favorites.push(bookId);
  }
  renderBooks();
  renderFavorites();
}
