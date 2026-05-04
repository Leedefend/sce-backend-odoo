import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const projectConfigPath = resolve(process.cwd(), 'dist/build/mp-weixin/project.config.json');
const privateConfigPath = resolve(process.cwd(), 'dist/build/mp-weixin/project.private.config.json');
const vendorPath = resolve(process.cwd(), 'dist/build/mp-weixin/common/vendor.js');

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf8'));
}

function writeJson(path, value) {
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

const projectConfig = readJson(projectConfigPath);
let privateConfig = {};
try {
  privateConfig = readJson(privateConfigPath);
} catch {
  privateConfig = {};
}

projectConfig.setting = {
  ...(projectConfig.setting || {}),
  enableUpdateWxAppCode: false,
  enhance: false,
  es6: true,
  urlCheck: false,
};

projectConfig.libVersion = projectConfig.libVersion || privateConfig.libVersion || '3.15.1';
projectConfig.appid = projectConfig.appid || 'touristappid';
projectConfig.projectname = projectConfig.projectname || 'SCE Mobile';

writeJson(projectConfigPath, projectConfig);

if (existsSync(vendorPath)) {
  const vendorCode = readFileSync(vendorPath, 'utf8');
  const dcloudPreloadAssetsBlock =
    '!function(){if(d(wx.preloadAssets)){const e=String.fromCharCode(99,100,110,49,46,100,99,108,111,117,100,46,110,101,116,46,99,110);setTimeout(()=>{wx.preloadAssets({data:[{type:"image",src:"https://"+e+"/55304e46/img/shadow-grey.png"}]})},3e3)}}(),';
  const patchedVendorCode = vendorCode.replace(
    dcloudPreloadAssetsBlock,
    '',
  );
  if (patchedVendorCode !== vendorCode) {
    writeFileSync(vendorPath, patchedVendorCode, 'utf8');
  }
}
