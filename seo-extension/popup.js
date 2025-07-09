const themeSwitch = document.getElementById('themeToggleSwitch');
const themeLabel = document.getElementById('themeLabel');

themeSwitch.addEventListener('change', () => {
    const isLight = themeSwitch.checked;
    document.body.classList.toggle('light-theme', isLight);
    themeLabel.innerHTML = isLight ? '☀️ Light Mode' : '🌙 Dark Mode';
});

function showLoader() {
    return `
        <div class="spinner">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>`;
}

async function analyze() {
    const keyword = document.getElementById('keyword').value.trim();
    const output = document.getElementById('output');
    output.innerHTML = showLoader();

    if (!keyword) {
        output.innerHTML = '<p class="text-danger p-2">❌ Please enter a keyword.</p>';
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/seo?q=${encodeURIComponent(keyword)}`);
        const data = await response.json();

        if (data.error) {
            output.innerHTML = '<p class="text-danger p-2">❌ Error: ' + data.error + '</p>';
        } else {
            const suggestions = data.primary_keywords;
            let html = '';
            suggestions.forEach((kw) => {
                html += `
              <div class="search-result">
                <h6><a href="https://www.google.com/search?q=${encodeURIComponent(kw.keyword)}" target="_blank">${kw.keyword}</a></h6>
                <p>📈 Volume: ${kw.search_volume} | 💰 CPC: $${kw.cpc} | ⚖️ Difficulty: ${kw.difficulty}</p>
                <p>📊 Competition: ${kw.competition} | 🧭 Trend: ${kw.trend} | 🔎 Category: ${kw.category}</p>
              </div>
            `;
            });
            output.innerHTML = html;
        }
    } catch (err) {
        output.innerHTML = '<p class="text-danger p-2">❌ Could not connect to backend.</p>';
    }
}