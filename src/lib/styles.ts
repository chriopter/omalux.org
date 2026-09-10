interface Bundle {
  version: number;
  name: string;
  group: string;
  description: string;
  modules: { name: string; enabled: boolean }[];
  preview: { width: number; height: number; source: string; darktable_version: string };
}

// Build-time discovery: each JSON file and its sibling image form one bundle.
const bundles = import.meta.glob<Bundle>('../../public/styles/**/style.json', {
  eager: true, import: 'default',
});
const images = import.meta.glob('../../public/styles/**/preview.webp', { query: '?url', import: 'default' });
const rank: Record<string, number> = { Essentials: 0, Monochrome: 1, Film: 2, Experimental: 4 };
const styles = Object.entries(bundles).map(([path, bundle]) => {
  const id = path.slice('../../public/styles/'.length, -'/style.json'.length);
  if (bundle.version !== 1 || !bundle.name || !bundle.group ||
      !Array.isArray(bundle.modules) || !bundle.preview?.width || !bundle.preview?.height) {
    throw new Error(`Invalid style bundle: ${path}`);
  }
  if (!images[`../../public/styles/${id}/preview.webp`]) {
    throw new Error(`Missing preview for style: ${id}`);
  }
  return {
    id, name: bundle.name, group: bundle.group, description: bundle.description,
    modules: bundle.modules, width: bundle.preview.width, height: bundle.preview.height,
    image: `/styles/${id.split('/').map(encodeURIComponent).join('/')}/preview.webp`,
  };
});
styles.sort((a, b) => (rank[a.group] ?? 3) - (rank[b.group] ?? 3) ||
  a.group.localeCompare(b.group) || Number(a.id !== 'neutral') - Number(b.id !== 'neutral') ||
  a.name.localeCompare(b.name));
if (!styles.length) throw new Error('No style bundles found');
export default { original: { image: '/styles/original.webp' }, styles };
