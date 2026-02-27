const boxOptions = [
  { id: 'foundation', label: 'Утеплённый фундамент', pct: 0.12, default: true },
  { id: 'walls', label: 'Наружные стены premium', pct: 0.15, default: true },
  { id: 'roof', label: 'Кровля металл + утепление', pct: 0.1, default: true }
];

const warmOptions = [
  { id: 'windows', label: 'Панорамные окна', pct: 0.08, default: true },
  { id: 'facade', label: 'Фасад с декоративной отделкой', pct: 0.1, default: true },
  { id: 'engineering', label: 'Инженерия (электрика + сантехника)', pct: 0.14, default: false }
];

const addonOptions = [
  { id: 'interior', label: 'Чистовая отделка', pct: 0.2, default: false },
  { id: 'terrace', label: 'Терраса и крыльцо', pct: 0.07, default: false },
  { id: 'landscape', label: 'Благоустройство участка', pct: 0.06, default: false }
];

function renderOptions(containerId, options) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = options.map((option) => `
    <label class="check-row">
      <input type="checkbox" data-pct="${option.pct}" id="${option.id}" ${option.default ? 'checked' : ''}>
      <span>${option.label}</span>
      <small>+${Math.round(option.pct * 100)}%</small>
    </label>
  `).join('');
}

function formatNumber(value) {
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value);
}

function calculateTotal() {
  const area = Number(document.getElementById('actual_space')?.value || 0);
  const baseRate = Number(document.getElementById('base_rate')?.value || 0);
  const baseCost = area * baseRate;

  const allChecks = document.querySelectorAll('input[type="checkbox"][data-pct]');
  let extraCost = 0;
  const selected = [];

  allChecks.forEach((check) => {
    if (check.checked) {
      const pct = Number(check.dataset.pct);
      const optionCost = baseCost * pct;
      extraCost += optionCost;
      selected.push(`${check.parentElement.querySelector('span').textContent}: ${formatNumber(optionCost)}`);
    }
  });

  const total = baseCost + extraCost;

  const totalPretty = document.getElementById('totalPretty');
  const breakdown = document.getElementById('breakdown');

  if (totalPretty) totalPretty.textContent = formatNumber(total);
  if (breakdown) {
    breakdown.innerHTML = `
      <p>База: ${formatNumber(baseCost)}</p>
      <p>Опции: ${formatNumber(extraCost)}</p>
      ${selected.length ? `<details><summary>Расшифровка</summary><ul>${selected.map((item) => `<li>${item}</li>`).join('')}</ul></details>` : ''}
    `;
  }
}

renderOptions('controlsBox', boxOptions);
renderOptions('controlsWarm', warmOptions);
renderOptions('addons', addonOptions);

document.addEventListener('input', (event) => {
  if (event.target.matches('#actual_space, #base_rate, input[type="checkbox"][data-pct]')) {
    calculateTotal();
  }
});

calculateTotal();
