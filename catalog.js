const grid = document.getElementById('projectsGrid');
const emptyState = document.getElementById('emptyState');
const servicesGrid = document.getElementById('servicesGrid');

const filters = {
  area: document.getElementById('areaFilter'),
  floors: document.getElementById('floorsFilter'),
  bedrooms: document.getElementById('bedroomsFilter'),
  budget: document.getElementById('budgetFilter')
};

function matchesArea(project, area) {
  if (area === 'small') return project.area < 120;
  if (area === 'medium') return project.area >= 120 && project.area <= 180;
  if (area === 'large') return project.area > 180;
  return true;
}

function matchesBudget(project, budget) {
  if (budget === 'low') return project.price < 8000000;
  if (budget === 'mid') return project.price >= 8000000 && project.price <= 12000000;
  if (budget === 'high') return project.price > 12000000;
  return true;
}

function renderCards(data) {
  grid.innerHTML = data
    .map((project) => `
      <article class="project-card">
        <img class="project-image" src="${project.previewImage}" alt="${project.name}">
        <div class="project-content">
          <h3>${project.name}</h3>
          <p>${project.style} • ${project.area} м² • ${project.floors} этаж(а)</p>
          <p>${project.bedrooms} спальни • ${project.bathrooms} санузла(ов)</p>
          <p>${project.description}</p>
          <p class="card-price">от ${formatPrice(project.price)}</p>
          <a class="btn btn-secondary" href="project.html?id=${project.id}">Подробнее</a>
        </div>
      </article>
    `)
    .join('');

  emptyState.hidden = data.length !== 0;
}

function renderServices() {
  if (!servicesGrid) return;
  servicesGrid.innerHTML = services.map((item) => `
    <article class="service-card">
      <h3>${item.title}</h3>
      <p>${item.text}</p>
    </article>
  `).join('');
}

function applyFilters() {
  const result = projects.filter((project) => {
    const floorsPass = filters.floors.value === 'all' || project.floors === Number(filters.floors.value);
    const bedroomsPass = filters.bedrooms.value === 'all' || project.bedrooms >= Number(filters.bedrooms.value);
    return (
      matchesArea(project, filters.area.value)
      && floorsPass
      && bedroomsPass
      && matchesBudget(project, filters.budget.value)
    );
  });

  renderCards(result);
}

Object.values(filters).forEach((element) => {
  element.addEventListener('change', applyFilters);
});

renderCards(projects);
renderServices();
