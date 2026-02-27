const params = new URLSearchParams(window.location.search);
const id = params.get('id');
const project = projects.find((item) => item.id === id) || projects[0];

const packageTemplates = [
  {
    name: 'Базовая комплектация «Коробка»',
    details: [
      'Геодезическая разбивка и подготовка участка',
      'Фундамент (плита/лента по проекту)',
      'Несущие стены и межэтажные перекрытия',
      'Кровля с утеплением и водосточной системой'
    ]
  },
  {
    name: 'Стандарт «Тёплый контур»',
    details: [
      'Энергоэффективные окна и входные двери',
      'Фасадная отделка и утепление наружного контура',
      'Черновые инженерные сети (электрика, вода, канализация)',
      'Подготовка под чистовую отделку помещений'
    ]
  },
  {
    name: 'Премиум «Под ключ»',
    details: [
      'Чистовая отделка стен, полов и потолков',
      'Установка сантехники, котельной и системы отопления',
      'Монтаж освещения и встроенной мебели по проекту',
      'Террасы, входные группы и базовое благоустройство участка'
    ]
  }
];

const planExamplesFallback = [
  {
    title: 'Пример: планировка с мастер-блоком',
    image: 'https://images.unsplash.com/photo-1600607687646-0f9f7d4f4f16?auto=format&fit=crop&w=1200&q=80'
  },
  {
    title: 'Пример: дневная зона + кабинет',
    image: 'https://images.unsplash.com/photo-1600210491369-e753d80a41f3?auto=format&fit=crop&w=1200&q=80'
  },
  {
    title: 'Пример: семейная зона 2 этажа',
    image: 'https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=1200&q=80'
  }
];

const additionalVisualsFallback = [
  {
    title: 'Фасад со стороны террасы',
    image: 'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80'
  },
  {
    title: 'Вид дома в вечернее время',
    image: 'https://images.unsplash.com/photo-1600585154205-2721f4f6f3dd?auto=format&fit=crop&w=1200&q=80'
  },
  {
    title: 'Ландшафт и входная группа',
    image: 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80'
  }
];

document.getElementById('projectTitle').textContent = project.name;
document.getElementById('projectMeta').textContent = `${project.style} • ${project.area} м² • ${project.floors} этаж(а) • ${project.bedrooms} спальни • ${project.bathrooms} санузла(ов)`;
document.getElementById('projectDescription').textContent = project.description;
document.getElementById('basePrice').textContent = `от ${formatPrice(project.price)}`;
document.getElementById('actual_space').value = project.area;
document.getElementById('base_rate').value = Math.round(project.price / project.area);

document.getElementById('specs').innerHTML = project.specs
  .map((spec) => `<li>${spec}</li>`)
  .join('');

const gallery = document.getElementById('gallery');
gallery.innerHTML = project.visualizations
  .map((image, index) => `
    <figure class="gallery-item">
      <img src="${image}" alt="${project.name} — визуализация ${index + 1}">
      <figcaption>Визуализация ${index + 1}</figcaption>
    </figure>
  `)
  .join('');

const plans = document.getElementById('plans');
plans.innerHTML = project.plans
  .map((plan) => `
    <figure class="plan-item">
      <img src="${plan.image}" alt="${project.name} — ${plan.title}">
      <figcaption>${plan.title}</figcaption>
    </figure>
  `)
  .join('');

const planExamples = document.getElementById('planExamples');
const examples = project.planExamples || planExamplesFallback;
planExamples.innerHTML = examples
  .map((plan) => `
    <figure class="plan-item alt-plan">
      <img src="${plan.image}" alt="${project.name} — ${plan.title}">
      <figcaption>${plan.title}</figcaption>
    </figure>
  `)
  .join('');

const additionalVisuals = document.getElementById('additionalVisuals');
const visuals = project.additionalVisuals || additionalVisualsFallback;
additionalVisuals.innerHTML = visuals
  .map((item) => `
    <figure class="gallery-item alt-visual">
      <img src="${item.image}" alt="${project.name} — ${item.title}">
      <figcaption>${item.title}</figcaption>
    </figure>
  `)
  .join('');

const packages = document.getElementById('packages');
packages.innerHTML = packageTemplates
  .map((pack) => `
    <article class="package-card">
      <h3>${pack.name}</h3>
      <ul>
        ${pack.details.map((item) => `<li>${item}</li>`).join('')}
      </ul>
    </article>
  `)
  .join('');
