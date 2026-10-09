interface Style { id: string; name: string; group: string; description: string; image: string; modules: {name: string; enabled: boolean}[]; }
const catalog = JSON.parse(document.querySelector('#style-data')!.textContent!) as {original: {image: string}; styles: Style[]};
const search = document.querySelector<HTMLInputElement>('#style-search')!;
const cards = [...document.querySelectorAll<HTMLButtonElement>('.style-card')];
const filters = [...document.querySelectorAll<HTMLButtonElement>('.filter')];
const subfilterRows = [...document.querySelectorAll<HTMLElement>('.subfilters')];
const subfilters = [...document.querySelectorAll<HTMLButtonElement>('.subfilter')];
const groups = [...document.querySelectorAll<HTMLElement>('.style-group')];
const count = document.querySelector('#style-count')!;
const original = document.querySelector<HTMLButtonElement>('#original-toggle')!;
let family = 'all';
let subgroup = '';
function filter() {
    const query = search.value.trim().toLowerCase();
    // While every family is listed, a large one shows its first looks and a way to the rest.
    const shortened = family === 'all' && !query;
    let found = 0;
    for (const section of groups) {
        let matches = 0;
        for (const block of section.querySelectorAll<HTMLElement>('.subgroup')) {
            let shown = 0;
            for (const card of block.querySelectorAll<HTMLButtonElement>('.style-card')) {
                const match = (family === 'all' || (section.dataset.family === family && (!subgroup || block.dataset.subgroup === subgroup))) &&
                    card.dataset.search!.includes(query);
                card.hidden = !match || (shortened && card.dataset.more !== undefined);
                if (match) matches++;
                if (!card.hidden) shown++;
            }
            block.hidden = shown === 0;
        }
        section.hidden = matches === 0;
        const more = section.querySelector<HTMLElement>('.show-family');
        if (more) more.hidden = !shortened;
        found += matches;
    }
    for (const button of filters) button.setAttribute('aria-pressed', String(button.dataset.family === family));
    for (const row of subfilterRows) row.hidden = row.dataset.family !== family;
    for (const button of subfilters) button.setAttribute('aria-pressed', String(button.dataset.subgroup === subgroup));
    count.textContent = `${found} ${found === 1 ? 'look' : 'looks'}`;
    document.querySelector<HTMLElement>('#no-styles')!.hidden = found !== 0;
}
// The address keeps the chosen family, so /styles#dhh opens on it.
function choose(nextFamily: string, nextSubgroup = '', remember = true) {
    family = filters.some(button => button.dataset.family === nextFamily) ? nextFamily : 'all';
    subgroup = subfilters.some(button => button.closest<HTMLElement>('.subfilters')!.dataset.family === family &&
        button.dataset.subgroup === nextSubgroup) ? nextSubgroup : '';
    filter();
    if (remember) history.replaceState(null, '', family === 'all' ? location.pathname : `#${family}${subgroup ? `/${subgroup}` : ''}`);
}
function fromAddress() {
    const [nextFamily = '', nextSubgroup = ''] = decodeURIComponent(location.hash.slice(1)).split('/');
    choose(nextFamily || 'all', nextSubgroup, false);
}
search.addEventListener('input', filter);
for (const button of filters) button.addEventListener('click', () => choose(button.dataset.family!));
for (const button of subfilters) button.addEventListener('click', () => choose(family, button.dataset.subgroup!));
for (const button of document.querySelectorAll<HTMLButtonElement>('.show-family')) button.addEventListener('click', () => {
    choose(button.dataset.family!);
    document.querySelector('.gallery')!.scrollIntoView();
});
addEventListener('hashchange', fromAddress);
fromAddress();
document.querySelector('#clear-filters')!.addEventListener('click', () => {search.value = '';choose('all');search.focus();});
original.addEventListener('click', () => {
    const show = original.getAttribute('aria-pressed') !== 'true';
    original.setAttribute('aria-pressed', String(show));
    original.innerHTML = `<span aria-hidden="true">◐</span> ${show ? 'Show styles' : 'Show original'}`;
    for (const card of cards) {
        const image = card.querySelector('img')!;
        // Keep each look's own sources aside while every card shows the one original.
        image.dataset.preview ??= image.getAttribute('src')!;
        if (image.hasAttribute('srcset')) image.dataset.previewSet ??= image.getAttribute('srcset')!;
        if (show) image.removeAttribute('srcset');
        else if (image.dataset.previewSet) image.setAttribute('srcset', image.dataset.previewSet);
        image.src = show ? catalog.original.image : image.dataset.preview;
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
