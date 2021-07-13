const resource = [

  /* --- CSS --- */
  '/autotrader/assets/css/style.css',

  /* --- JavaScripts --- */
  
  '/autotrader/assets/js/dist/home.min.js',
  '/autotrader/assets/js/dist/page.min.js',
  '/autotrader/assets/js/dist/post.min.js',
  '/autotrader/assets/js/dist/categories.min.js',
  '/autotrader/assets/js/data/search.json',
  '/autotrader/app.js',
  '/autotrader/sw.js',

  /* --- HTML --- */
  '/autotrader/index.html',
  '/autotrader/404.html',
  
    '/autotrader/categories/',
  
    '/autotrader/tags/',
  
    '/autotrader/archives/',
  
    '/autotrader/about/',
  

  /* --- Favicons --- */
  

  '/autotrader/assets/img/favicons/android-chrome-192x192.png',
  '/autotrader/assets/img/favicons/android-chrome-512x512.png',
  '/autotrader/assets/img/favicons/apple-touch-icon.png',
  '/autotrader/assets/img/favicons/favicon-16x16.png',
  '/autotrader/assets/img/favicons/favicon-32x32.png',
  '/autotrader/assets/img/favicons/favicon.ico',
  '/autotrader/assets/img/favicons/mstile-150x150.png',
  '/autotrader/assets/img/favicons/site.webmanifest',
  '/autotrader/assets/img/favicons/browserconfig.xml'

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

