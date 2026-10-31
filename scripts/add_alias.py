with open('frontend/static/js/app.js', 'r', encoding='utf-8') as f:
    c = f.read()

if 'window.switchScreen' not in c:
    c = c.replace('function navigateTo(', 'window.switchScreen = function(id) { return navigateTo(id); };\nfunction navigateTo(')
    with open('frontend/static/js/app.js', 'w', encoding='utf-8') as f:
        f.write(c)
    print('Added switchScreen alias')
else:
    print('Already present')

