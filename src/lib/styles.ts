interface Bundle {
  version: number;
  name: string;
  group: string;
  family?: string;
  subgroup?: string;
  description: string;
  modules: { name: string; enabled: boolean }[];
  preview: { width: number; height: number; source: string; darktable_version: string };
}

// Build-time discovery: each JSON file and its sibling images form one bundle.
const bundles = import.meta.glob<Bundle>('../../public/styles/**/style.json', {
  eager: true, import: 'default',
});
const images = import.meta.glob('../../public/styles/**/{preview,thumb}.webp', { query: '?url', import: 'default' });
const rank: Record<string, number> = { Essentials: 0, Monochrome: 1, Film: 2, Experimental: 4 };
// What a family is, where its name does not say it.
const notes: Record<string, string> = {
  DHH: 'Fitted to renderings of the DHH preset set on a standard camera profile.',
};
// A family this large gets a denser grid and is shortened while all families are shown.
const LARGE = 24;
const TEASER = 10;

const slug = (text: string) => text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
const styles = Object.entries(bundles).map(([path, bundle]) => {
  const id = path.slice('../../public/styles/'.length, -'/style.json'.length);
  if (bundle.version !== 1 || !bundle.name || !bundle.group ||
      !Array.isArray(bundle.modules) || !bundle.preview?.width || !bundle.preview?.height) {
    throw new Error(`Invalid style bundle: ${path}`);
  }
  if (!images[`../../public/styles/${id}/preview.webp`]) {
    throw new Error(`Missing preview for style: ${id}`);
  }
  // Catalogues generated before families were recorded carry "Family · Sub-group" only.
  const [first, ...rest] = bundle.group.split(' · ');
  const family = bundle.family ?? first;
  const subgroup = bundle.subgroup ?? rest.join(' · ');
  const url = `/styles/${id.split('/').map(encodeURIComponent).join('/')}`;
  return {
    id, name: bundle.name, family, subgroup, group: subgroup ? `${family} · ${subgroup}` : family,
    description: bundle.description,
    modules: bundle.modules, width: bundle.preview.width, height: bundle.preview.height,
    image: `${url}/preview.webp`,
    thumb: images[`../../public/styles/${id}/thumb.webp`] ? `${url}/thumb.webp` : null,
  };
});
const natural = new Intl.Collator('en', { numeric: true, sensitivity: 'base' });
styles.sort((a, b) => (rank[a.family] ?? 3) - (rank[b.family] ?? 3) ||
  natural.compare(a.family, b.family) || natural.compare(a.subgroup, b.subgroup) ||
  Number(a.id !== 'neutral') - Number(b.id !== 'neutral') || natural.compare(a.name, b.name));
if (!styles.length) throw new Error('No style bundles found');

const families = [...new Set(styles.map(style => style.family))].map(name => {
  const members = styles.filter(style => style.family === name);
  const subgroups = [...new Set(members.map(style => style.subgroup))].map(subgroup => ({
    name: subgroup, slug: slug(subgroup), styles: members.filter(style => style.subgroup === subgroup),
  }));
  return {
    name, slug: slug(name), note: notes[name] ?? '', count: members.length,
    large: members.length > LARGE, teaser: TEASER,
    // Sub-headings only where a family is actually divided.
    divided: subgroups.length > 1, subgroups,
  };
});
export default { original: { image: '/styles/original.webp' }, styles, families };
