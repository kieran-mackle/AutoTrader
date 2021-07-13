const resource = [

  /* --- CSS --- */
  '/AutoTrader/assets/css/style.css',

  /* --- JavaScripts --- */
  
  '/AutoTrader/assets/js/dist/home.min.js',
  '/AutoTrader/assets/js/dist/page.min.js',
  '/AutoTrader/assets/js/dist/post.min.js',
  '/AutoTrader/assets/js/dist/categories.min.js',
  '/AutoTrader/assets/js/data/search.json',
  '/AutoTrader/app.js',
  '/AutoTrader/sw.js',

  /* --- HTML --- */
  '/AutoTrader/index.html',
  '/AutoTrader/404.html',
  
    '/AutoTrader/categories/',
  
    '/AutoTrader/tags/',
  
    '/AutoTrader/archives/',
  
    '/AutoTrader/about/',
  

  /* --- Favicons --- */
  

  '/AutoTrader/assets/img/favicons/android-chrome-192x192.png',
  '/AutoTrader/assets/img/favicons/android-chrome-512x512.png',
  '/AutoTrader/assets/img/favicons/apple-touch-icon.png',
  '/AutoTrader/assets/img/favicons/favicon-16x16.png',
  '/AutoTrader/assets/img/favicons/favicon-32x32.png',
  '/AutoTrader/assets/img/favicons/favicon.ico',
  '/AutoTrader/assets/img/favicons/mstile-150x150.png',
  '/AutoTrader/assets/img/favicons/site.webmanifest',
  '/AutoTrader/assets/img/favicons/browserconfig.xml'

];

/* The request url with below domain will be cached */
const allowedDomains = [
  

  'localhost:4001',

  'fonts.gstatic.com',
  'fonts.googleapis.com',
  'cdn.jsdelivr.net',
  'polyfill.io'
];

/* Requests that include the following path will be banned */
const denyUrls = [
  
];

