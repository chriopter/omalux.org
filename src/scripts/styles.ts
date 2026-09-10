interface Style { id: string; name: string; group: string; description: string; image: string; modules: {name: string; enabled: boolean}[]; }
const catalog = JSON.parse(document.querySelector('#style-data')!.textContent!) as {original: {image: string}; styles: Style[]};
const search = document.querySelector<HTMLInputElement>('#style-search')!;
const cards = [...document.querySelectorAll<HTMLButtonElement>('.style-card')];
const filters = [...document.querySelectorAll<HTMLButtonElement>('.filter')];
const groups = [...document.querySelectorAll<HTMLElement>('.style-group')];
const count = document.querySelector('#style-count')!;
const original = document.querySelector<HTMLButtonElement>('#original-toggle')!;
let group = 'all';
function filter() {
    const query = search.value.trim().toLowerCase();
    let visible = 0;
    for (const section of groups) {
        let matches = 0;
        for (const card of section.querySelectorAll<HTMLButtonElement>('.style-card')) {
            card.hidden = !(group === 'all' || section.dataset.group === group) || !card.dataset.search!.includes(query);
            if (!card.hidden) matches++;
        }
        section.hidden = matches === 0;
        visible += matches;
    }
    for (const button of filters) button.setAttribute('aria-pressed', String(button.dataset.group === group));
    count.textContent = `${visible} ${visible === 1 ? 'look' : 'looks'}`;
    document.querySelector<HTMLElement>('#no-styles')!.hidden = visible !== 0;
}
search.addEventListener('input', filter);
for (const button of filters) button.addEventListener('click', () => {group = button.dataset.group!;filter();});
document.querySelector('#clear-filters')!.addEventListener('click', () => {group = 'all';search.value = '';filter();search.focus();});
original.addEventListener('click', () => {
    const show = original.getAttribute('aria-pressed') !== 'true';
    original.setAttribute('aria-pressed', String(show));
    original.innerHTML = `<span aria-hidden="true">◐</span> ${show ? 'Show styles' : 'Show original'}`;
    for (const card of cards) {
        const image = card.querySelector('img')!;
        image.src = show ? catalog.original.image : image.dataset.preview!;
        image.alt = show ? 'Original beach photograph' : `Beach photograph with ${catalog.styles.find(p => p.id === card.dataset.id)!.name} style`;
    }
});
const dialog = document.querySelector<HTMLDialogElement>('#style-dialog')!;
const range = document.querySelector<HTMLInputElement>('#comparison')!;
const frame = document.querySelector<HTMLElement>('.compare-frame')!;
let trigger: HTMLButtonElement | null = null;
function compare() {frame.style.setProperty('--reveal', `${range.value}%`);}
range.addEventListener('input', compare);
for (const card of cards) card.addEventListener('click', () => {
    const style = catalog.styles.find(p => p.id === card.dataset.id)!;
    trigger = card;
    document.querySelector('#detail-name')!.textContent = style.name;
    document.querySelector('#detail-group')!.textContent = style.group;
    document.querySelector('#detail-description')!.textContent = style.description;
    const after = document.querySelector<HTMLImageElement>('#detail-after')!;
    after.src = style.image; after.alt = `Beach photograph with ${style.name} style`;
    const modules = style.modules.filter(m => m.enabled);
    const list = document.querySelector('#detail-modules')!;
    list.replaceChildren(...modules.map(module => {const li = document.createElement('li');li.textContent = module.name;return li;}));
    document.querySelector('#module-count')!.textContent = `(${modules.length})`;
    dialog.querySelector('details')!.open = false;
    range.value = '50'; compare();
    dialog.showModal();
    document.body.style.overflow = 'hidden';
});
document.querySelector('#close-detail')!.addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
    const bounds = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom)) dialog.close();
});
dialog.addEventListener('close', () => {document.body.style.overflow = '';trigger?.focus();});
