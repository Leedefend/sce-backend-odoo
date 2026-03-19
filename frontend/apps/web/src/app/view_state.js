export function deriveListStatus({ error = '', recordsLength = 0 } = {}) {
  if (error) {
    return 'error';
  }
  if (!recordsLength) {
    return 'empty';
  }
  return 'ok';
}

export function deriveRecordStatus({ error = '', fieldsLength = 0 } = {}) {
  if (error) {
    return 'error';
  }
  if (!fieldsLength) {
    return 'empty';
  }
  return 'ok';
}
