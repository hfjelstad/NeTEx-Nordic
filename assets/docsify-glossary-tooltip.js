/**
 * docsify-glossary-tooltip.js
 * Parses the Glossary page and adds hover tooltips on first occurrence of each term.
 */
(function () {
  var GLOSSARY_PATH = 'Guides/Glossary/Glossary.md';
  var glossaryTerms = {};
  var glossaryLoaded = false;

  function parseGlossary(markdown) {
    var terms = {};
    var sections = markdown.split(/^## /m);
    sections.shift(); // remove content before first ##

    sections.forEach(function (section) {
      var lines = section.trim().split('\n');
      var term = lines[0].trim();
      if (!term) return;

      // Grab the first non-empty paragraph as definition
      var def = '';
      for (var i = 1; i < lines.length; i++) {
        var line = lines[i].trim();
        if (line === '' || line === '---') continue;
        if (line.startsWith('>') || line.startsWith('→')) continue;
        if (line) {
          def = line;
          break;
        }
      }
      if (def) {
        terms[term] = def;
      }
    });
    return terms;
  }

  function escapeRegExp(str) {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function addTooltips(html, terms) {
    var used = {};
    Object.keys(terms).sort(function (a, b) {
      return b.length - a.length; // longest first
    }).forEach(function (term) {
      if (used[term]) return;
      // Match whole word, not inside tags or code
      var re = new RegExp(
        '(?<![<\\w/])\\b(' + escapeRegExp(term) + ')\\b(?![^<]*>|[^<]*<\\/code>)',
        ''
      );
      var match = html.match(re);
      if (match) {
        var tooltip = terms[term].replace(/"/g, '&quot;');
        html = html.replace(re,
          '<span class="glossary-tooltip" title="' + tooltip + '">$1</span>'
        );
        used[term] = true;
      }
    });
    return html;
  }

  window.$docsify = window.$docsify || {};
  window.$docsify.plugins = (window.$docsify.plugins || []).concat(function (hook, vm) {
    hook.init(function () {
      // Fetch glossary markdown
      fetch(vm.router.getFile(GLOSSARY_PATH))
        .then(function (res) { return res.ok ? res.text() : ''; })
        .then(function (md) {
          glossaryTerms = parseGlossary(md);
          glossaryLoaded = true;
        })
        .catch(function () { glossaryLoaded = true; });
    });

    hook.afterEach(function (html) {
      if (!glossaryLoaded || Object.keys(glossaryTerms).length === 0) return html;
      // Don't annotate the glossary page itself
      if (vm.route.path && vm.route.path.indexOf('Glossary') !== -1) return html;
      return addTooltips(html, glossaryTerms);
    });
  });

  // Minimal tooltip CSS
  var style = document.createElement('style');
  style.textContent = [
    '.glossary-tooltip {',
    '  border-bottom: 1px dotted rgba(150,150,150,0.5);',
    '  cursor: help;',
    '  position: relative;',
    '}',
    '.glossary-tooltip:hover::after {',
    '  content: attr(title);',
    '  position: absolute;',
    '  bottom: 100%;',
    '  left: 0;',
    '  background: #1a1a2e;',
    '  color: #e0e0e0;',
    '  padding: 6px 10px;',
    '  border-radius: 4px;',
    '  font-size: 13px;',
    '  max-width: 320px;',
    '  white-space: normal;',
    '  z-index: 1000;',
    '  box-shadow: 0 2px 8px rgba(0,0,0,0.3);',
    '}'
  ].join('\n');
  document.head.appendChild(style);
})();
