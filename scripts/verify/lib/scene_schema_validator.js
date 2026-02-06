#!/usr/bin/env node
'use strict';

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function assertType(value, type) {
  if (type === 'array') return Array.isArray(value);
  if (type === 'object') return isObject(value);
  if (type === 'number') return typeof value === 'number' && !Number.isNaN(value);
  return typeof value === type;
}

function validateFields(obj, fields, prefix) {
  const errors = [];
  Object.entries(fields || {}).forEach(([key, spec]) => {
    const value = obj[key];
    const required = spec.required === true;
    if (value === undefined || value === null) {
      if (required) errors.push(`${prefix}${key} missing`);
      return;
    }
    if (spec.type && !assertType(value, spec.type)) {
      errors.push(`${prefix}${key} expected ${spec.type}`);
      return;
    }
    if (spec.fields && isObject(value)) {
      errors.push(...validateFields(value, spec.fields, `${prefix}${key}.`));
    }
    if (spec.item_fields && Array.isArray(value)) {
      value.forEach((item, idx) => {
        if (!isObject(item)) {
          errors.push(`${prefix}${key}[${idx}] expected object`);
          return;
        }
        errors.push(...validateFields(item, spec.item_fields, `${prefix}${key}[${idx}].`));
      });
    }
    if (spec.at_least_one && isObject(value)) {
      const ok = spec.at_least_one.some((field) => value[field] !== undefined && value[field] !== null);
      if (!ok) {
        errors.push(`${prefix}${key} missing any of ${spec.at_least_one.join(',')}`);
      }
    }
  });
  return errors;
}

function validateScene(scene, schema, profile) {
  const errors = [];
  const required = schema.required || [];
  required.forEach((key) => {
    if (scene[key] === undefined || scene[key] === null) {
      errors.push(`${key} missing`);
    }
  });
  errors.push(...validateFields(scene, schema.fields, ''));

  const profileRequired = (profile && profile.required) || [];
  profileRequired.forEach((key) => {
    if (scene[key] === undefined || scene[key] === null) {
      errors.push(`profile requires ${key}`);
    }
  });

  const lpProfile = (profile && profile.list_profile) || {};
  if (scene.list_profile && lpProfile.required) {
    lpProfile.required.forEach((key) => {
      if (scene.list_profile[key] === undefined || scene.list_profile[key] === null) {
        errors.push(`list_profile.${key} missing`);
      }
    });
  }
  if (scene.list_profile && Array.isArray(lpProfile.hidden_columns_must_include)) {
    const hidden = scene.list_profile.hidden_columns || [];
    lpProfile.hidden_columns_must_include.forEach((field) => {
      if (!hidden.includes(field)) {
        errors.push(`hidden_columns missing ${field}`);
      }
    });
  }

  return errors;
}

module.exports = {
  validateScene,
};
