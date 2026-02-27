const params = new URLSearchParams(window.location.search);
const id = params.get('id');
const project = projects.find((item) => item.id === id) || projects[0];

const packageTemplates = [
  {
    name: 'Базовая комплектация «Коробка»',
    lead: 'Оптимальный вариант для тех, кто хочет построить надёжный конструктив и завершать отделку поэтапно.',
    duration: 'Срок реализации: 3–5 месяцев',
    warranty: 'Гарантия: 5 лет на конструктив',
    included: [
      'Геодезическая разбивка и подготовка пятна застройки',
      'Фундамент (монолитная плита/лента по расчёту)',
      'Несущие стены и межэтажные перекрытия',
      'Стропильная система и кровля с утеплением',
      'Водосточная система и базовая гидроизоляция узлов'
    ],
    extra: [
      'Черновая разводка электрики',
      'Монтаж временных инженерных решений',
      'Консервация объекта на зимний период'
    ]
  },
  {
    name: 'Стандарт «Тёплый контур»',
    lead: 'Дом готов к круглогодичному закрытому контуру: можно сразу переходить к чистовой отделке.',
    duration: 'Срок реализации: 5–7 месяцев',
    warranty: 'Гарантия: 7 лет на конструктив и фасадный контур',
    included: [
      'Все работы из комплектации «Коробка»',
      'Энергоэффективные окна и входная дверь',
      'Утепление и фасадная отделка наружных стен',
      'Черновые инженерные сети (электрика, водоснабжение, канализация)',
      'Подготовка пола и стен под чистовую отделку'
    ],
    extra: [
      'Система приточно-вытяжной вентиляции',
      'Дополнительное фасадное освещение',
      'Подготовка под камин или печь'
    ]
  },
  {
    name: 'Премиум «Под ключ»',
    lead: 'Полностью готовый к проживанию загородный дом с инженерией, отделкой и благоустройством.',
    duration: 'Срок реализации: 7–10 месяцев',
    warranty: 'Гарантия: 10 лет на конструктив, 3 года на инженерные системы',
    included: [
      'Все работы из комплектации «Тёплый контур»',
      'Чистовая отделка (полы, стены, потолки)',
      'Полная комплектация котельной и системы отопления',
      'Установка сантехники, светильников и электрофурнитуры',
      'Террасы, входные группы и базовое благоустройство участка'
    ],
    extra: [
      'Система «умный дом»',
      'Ландшафтный дизайн и автополив',
      'Авторский интерьерный пакет'
    ]
  }
];

const planExamplesFallback = [
  {
    title: 'Пример: планировка с мастер-блоком',
    image: 'https://source.unsplash.com/1200x800/?floor-plan,architect'
  },
  {
    title: 'Пример: дневная зона + кабинет',
    image: 'https://source.unsplash.com/1200x800/?blueprint,architecture'
  },
  {
    title: 'Пример: семейная зона 2 этажа',
    image: 'https://source.unsplash.com/1200x800/?house-plan,drawing'
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
    <figure class="plan-item plan-drawing">
      <img src="${plan.image}" alt="${project.name} — ${plan.title}">
      <figcaption>${plan.title}</figcaption>
    </figure>
  `)
  .join('');

const planExamples = document.getElementById('planExamples');
const examples = project.planExamples || planExamplesFallback;
planExamples.innerHTML = examples
  .map((plan) => `
    <figure class="plan-item alt-plan plan-drawing">
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
    <article class="package-card package-card-detailed">
      <h3>${pack.name}</h3>
      <p class="package-lead">${pack.lead}</p>
      <p class="package-meta">${pack.duration}</p>
      <p class="package-meta">${pack.warranty}</p>
      <h4>Что входит:</h4>
      <ul>
        ${pack.included.map((item) => `<li>${item}</li>`).join('')}
      </ul>
      <h4>Опционально:</h4>
      <ul class="package-extra">
        ${pack.extra.map((item) => `<li>${item}</li>`).join('')}
      </ul>
    </article>
  `)
  .join('');
