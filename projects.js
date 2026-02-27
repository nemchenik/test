const projects = [
  {
    id: 'scandi-140',
    name: 'Сканди 140',
    area: 142,
    floors: 1,
    bedrooms: 3,
    bathrooms: 2,
    price: 7900000,
    style: 'Скандинавский',
    description: 'Компактный одноэтажный дом с большой кухней-гостиной, мастер-спальней и террасой для отдыха.',
    previewImage: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1512918728675-ed5a9ecdebfd?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?auto=format&fit=crop&w=1200&q=80'
    ],
    plans: [
      { title: 'План 1 этажа', image: 'https://images.unsplash.com/photo-1600607687644-c7f34b5f7f54?auto=format&fit=crop&w=1200&q=80' }
    ],
    specs: ['Кухня-гостиная 42 м²', '3 спальни', 'Терраса 26 м²', 'Панорамные окна']
  },
  {
    id: 'barn-186',
    name: 'Барн 186',
    area: 186,
    floors: 2,
    bedrooms: 4,
    bathrooms: 3,
    price: 11900000,
    style: 'Barnhouse',
    description: 'Популярный двухэтажный barnhouse с вторым светом, кабинетом и мастер-блоком.',
    previewImage: 'https://images.unsplash.com/photo-1600566752355-35792bedcfea?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://images.unsplash.com/photo-1600047509358-9dc75507daeb?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1560185007-c5ca9d2c014d?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600573472550-8090b5e0745e?auto=format&fit=crop&w=1200&q=80'
    ],
    plans: [
      { title: 'План 1 этажа', image: 'https://images.unsplash.com/photo-1600607687646-0f9f7d4f4f16?auto=format&fit=crop&w=1200&q=80' },
      { title: 'План 2 этажа', image: 'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80' }
    ],
    specs: ['Кухня-гостиная 54 м²', '4 спальни', 'Сауна', 'Второй свет']
  },
  {
    id: 'zagorod-203',
    name: 'Загородный дом 203',
    area: 203,
    floors: 2,
    bedrooms: 4,
    bathrooms: 3,
    price: 13700000,
    style: 'Классика + современный',
    description: 'Просторный загородный дом для постоянного проживания: отдельная мастер-зона, кабинет и большая терраса.',
    previewImage: 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://source.unsplash.com/1200x800/?country-house,facade',
      'https://source.unsplash.com/1200x800/?suburban-house,exterior',
      'https://source.unsplash.com/1200x800/?modern-cottage,house'
    ],
    plans: [
      { title: 'План 1 этажа: гостиная 48 м², кухня-столовая, кабинет', image: 'https://source.unsplash.com/1200x800/?floor-plan,architectural-drawing' },
      { title: 'План 2 этажа: 4 спальни, гардеробные, 2 санузла', image: 'https://source.unsplash.com/1200x800/?blueprint,house-plan' }
    ],
    specs: ['Площадь 203 м²', '4 спальни + кабинет', '3 санузла', 'Терраса 34 м²'],
    planExamples: [
      { title: 'Вариант А: кухня-гостиная + кабинет на 1 этаже', image: 'https://source.unsplash.com/1200x800/?floor-plan,home' },
      { title: 'Вариант B: мастер-спальня с гардеробной', image: 'https://source.unsplash.com/1200x800/?architecture-plan,drawing' },
      { title: 'Вариант C: детские спальни и семейный холл', image: 'https://source.unsplash.com/1200x800/?construction-blueprint,plan' }
    ],
    additionalVisuals: [
      { title: 'Фасад с панорамным остеклением', image: 'https://source.unsplash.com/1200x800/?country-house,day' },
      { title: 'Терраса и зона отдыха', image: 'https://source.unsplash.com/1200x800/?country-house,terrace' },
      { title: 'Вечерняя подсветка дома', image: 'https://source.unsplash.com/1200x800/?country-house,night' }
    ]
  },
  {
    id: 'neo-220',
    name: 'Нео 220',
    area: 224,
    floors: 2,
    bedrooms: 5,
    bathrooms: 3,
    price: 15400000,
    style: 'Современный',
    description: 'Большой современный дом для семьи с 4+ детьми и просторной приватной зоной.',
    previewImage: 'https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://images.unsplash.com/photo-1600210492486-724fe5c67fb3?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600573472592-401b489a3cdc?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?auto=format&fit=crop&w=1200&q=80'
    ],
    plans: [
      { title: 'План 1 этажа', image: 'https://images.unsplash.com/photo-1600210491369-e753d80a41f3?auto=format&fit=crop&w=1200&q=80' },
      { title: 'План 2 этажа', image: 'https://images.unsplash.com/photo-1600566753376-12c8ab7fb75b?auto=format&fit=crop&w=1200&q=80' }
    ],
    specs: ['5 спален', 'Кабинет', 'Гараж на 2 авто', 'Каминный зал']
  },
  {
    id: 'terra-118',
    name: 'Терра 118',
    area: 118,
    floors: 1,
    bedrooms: 2,
    bathrooms: 1,
    price: 6950000,
    style: 'Минимализм',
    description: 'Рациональный дом для пары или небольшой семьи с продуманной инженерией.',
    previewImage: 'https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://images.unsplash.com/photo-1605146769289-440113cc3d00?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600585152915-d208bec867a1?auto=format&fit=crop&w=1200&q=80'
    ],
    plans: [
      { title: 'План 1 этажа', image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80' }
    ],
    specs: ['2 спальни', 'Кухня-гостиная 36 м²', 'Котельная', 'Навес для авто']
  },
  {
    id: 'alpine-164',
    name: 'Альпина 164',
    area: 164,
    floors: 2,
    bedrooms: 4,
    bathrooms: 2,
    price: 10200000,
    style: 'Шале',
    description: 'Тёплый семейный дом в стиле шале: много дерева, просторная гостиная и большие свесы кровли.',
    previewImage: 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600607687644-c7f34b5f7f54?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?auto=format&fit=crop&w=1200&q=80'
    ],
    plans: [
      { title: 'План 1 этажа', image: 'https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=1200&q=80' },
      { title: 'План 2 этажа', image: 'https://images.unsplash.com/photo-1600566752355-35792bedcfea?auto=format&fit=crop&w=1200&q=80' }
    ],
    specs: ['4 спальни', '2 санузла', 'Котельная', 'Терраса 30 м²']
  },
  {
    id: 'river-96',
    name: 'Ривер 96',
    area: 96,
    floors: 1,
    bedrooms: 2,
    bathrooms: 1,
    price: 5750000,
    style: 'Современный компакт',
    description: 'Небольшой дом для дачи или постоянного проживания: быстрая стройка и низкая стоимость владения.',
    previewImage: 'https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&w=1200&q=80',
    visualizations: [
      'https://images.unsplash.com/photo-1600585152220-90363fe7e115?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1600585152915-d208bec867a1?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1523217582562-09d0def993a6?auto=format&fit=crop&w=1200&q=80'
    ],
    plans: [
      { title: 'План 1 этажа', image: 'https://images.unsplash.com/photo-1600607688969-a5bfcd646154?auto=format&fit=crop&w=1200&q=80' }
    ],
    specs: ['2 спальни', 'Кухня-гостиная 30 м²', 'Постирочная', 'Тёплый контур']
  }
];

const services = [
  {
    title: 'Индивидуальное проектирование',
    text: 'Адаптируем любой проект под ваш участок, состав семьи и бюджет.'
  },
  {
    title: 'Строительство «под ключ»',
    text: 'Берём на себя все этапы: фундамент, коробка, инженерия, чистовая отделка.'
  },
  {
    title: 'Инженерные системы',
    text: 'Проектируем и монтируем отопление, вентиляцию, водоснабжение и электрику.'
  },
  {
    title: 'Ландшафт и благоустройство',
    text: 'Террасы, дорожки, освещение, заборы и озеленение участка.'
  }
];

function formatPrice(value) {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    maximumFractionDigits: 0
  }).format(value);
}
