export function validateSceneRegistry(scenes) {
  const errors = [];
  const validScenes = [];
  const seenKeys = new Set();
  const seenRoutes = new Set();

  if (!Array.isArray(scenes)) {
    return { validScenes: [], errors: [{ index: -1, issues: ['scenes must be an array'] }] };
  }

  scenes.forEach((scene, index) => {
    const issues = [];
    if (!scene || typeof scene !== 'object') {
      issues.push('scene must be an object');
    }
    const key = scene && scene.key;
    const label = scene && scene.label;
    const route = scene && scene.route;
    const target = scene && scene.target;

    if (!key || typeof key !== 'string') {
      issues.push('key is required');
    } else if (seenKeys.has(key)) {
      issues.push('duplicate key');
    }

    if (!label || typeof label !== 'string') {
      issues.push('label is required');
    }

    if (!route || typeof route !== 'string') {
      issues.push('route is required');
    } else if (seenRoutes.has(route)) {
      issues.push('duplicate route');
    }

    if (!target || typeof target !== 'object') {
      issues.push('target is required');
    }

    if (issues.length) {
      errors.push({ index, key: key || null, route: route || null, issues });
      return;
    }

    seenKeys.add(key);
    seenRoutes.add(route);
    validScenes.push(scene);
  });

  return { validScenes, errors };
}
