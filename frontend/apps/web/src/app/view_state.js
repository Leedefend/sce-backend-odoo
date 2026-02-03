export function deriveListStatus({ error, recordsLength }) {
  if (error) {
    return 'error';
  }
  if (!recordsLength) {
    return 'empty';
  }
  return 'ok';
}

export function deriveRecordStatus({ error, fieldsLength }) {
  if (error) {
    return 'error';
  }
  if (!fieldsLength) {
    return 'empty';
  }
  return 'ok';
}
