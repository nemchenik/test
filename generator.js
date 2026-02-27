const genArea = document.getElementById('genArea');
const genFloors = document.getElementById('genFloors');
const genBedrooms = document.getElementById('genBedrooms');
const genStyle = document.getElementById('genStyle');
const genRate = document.getElementById('genRate');
const genGarage = document.getElementById('genGarage');
const genTerrace = document.getElementById('genTerrace');
const genPremium = document.getElementById('genPremium');

function formatRub(value) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(value);
}

function pickDemoProject() {
  const area = Number(genArea.value);
  const floors = Number(genFloors.value);
  const bedrooms = Number(genBedrooms.value);

  return projects.find((project) =>
    Math.abs(project.area - area) <= 45
    && project.floors === floors
    && project.bedrooms >= bedrooms
  ) || projects[0];
}

function renderGenerator() {
  const project = pickDemoProject();
  const area = Number(genArea.value);

  document.getElementById('genTitle').textContent = `Проект: ${project.name}`;
  document.getElementById('genMeta').textContent = `${genStyle.value} • ${area} м² • ${genFloors.value} этаж(а) • ${genBedrooms.value} спальни`;

  document.getElementById('genVisuals').innerHTML = project.visualizations
    .slice(0, 2)
    .map((image, index) => `
      <figure class="gallery-item alt-visual">
        <img src="${image}" alt="${project.name} визуализация ${index + 1}">
        <figcaption>Визуализация ${index + 1}</figcaption>
      </figure>
    `)
    .join('');

  document.getElementById('genPlans').innerHTML = project.plans
    .slice(0, 2)
    .map((plan) => `
      <figure class="plan-item alt-plan">
        <img src="${plan.image}" alt="${plan.title}">
        <figcaption>${plan.title}</figcaption>
      </figure>
    `)
    .join('');

  const base = area * Number(genRate.value);
  let extrasPct = 0;
  if (genGarage.checked) extrasPct += 0.08;
  if (genTerrace.checked) extrasPct += 0.06;
  if (genPremium.checked) extrasPct += 0.09;

  const extras = base * extrasPct;
  const total = base + extras;

  document.getElementById('genBase').textContent = formatRub(base);
  document.getElementById('genExtras').textContent = formatRub(extras);
  document.getElementById('genTotal').textContent = `Итого: ${formatRub(total)}`;
}

document.addEventListener('input', (event) => {
  if (event.target.matches('#genArea, #genFloors, #genBedrooms, #genStyle, #genRate, #genGarage, #genTerrace, #genPremium')) {
    renderGenerator();
  }
});

renderGenerator();
