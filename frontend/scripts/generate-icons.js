#!/usr/bin/env node
/**
 * Generate PWA icons from source 512x512 PNG.
 * Run: npm run generate-icons
 * Requires: npm install sharp --save-dev
 */

const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const ICONS_DIR = path.join(__dirname, '../public/icons');
const SPLASH_DIR = path.join(__dirname, '../public/splash');
const SOURCE_ICON = path.join(ICONS_DIR, 'icon-512x512.png');

const ICON_SIZES = [16, 32, 72, 96, 128, 144, 152, 180, 192, 384, 512];
const MASKABLE_SIZES = [192, 512];

const SPLASH_SCREENS = [
  { width: 2048, height: 2732, name: 'apple-splash-2048-2732.png' },
  { width: 1668, height: 2388, name: 'apple-splash-1668-2388.png' },
  { width: 1290, height: 2796, name: 'apple-splash-1290-2796.png' },
  { width: 1179, height: 2556, name: 'apple-splash-1179-2556.png' },
  { width: 1170, height: 2532, name: 'apple-splash-1170-2532.png' },
];

async function generateIcon(size) {
  const output = path.join(ICONS_DIR, `icon-${size}x${size}.png`);
  await sharp(SOURCE_ICON)
    .resize(size, size)
    .png()
    .toFile(output);
  console.log(`Generated: icon-${size}x${size}.png`);
}

async function generateMaskableIcon(size) {
  const innerSize = Math.floor(size * 0.8);
  const padding = Math.floor((size - innerSize) / 2);

  const resizedIcon = await sharp(SOURCE_ICON)
    .resize(innerSize, innerSize)
    .toBuffer();

  const background = await sharp({
    create: {
      width: size,
      height: size,
      channels: 4,
      background: { r: 14, g: 165, b: 233, alpha: 1 },
    },
  })
    .composite([{
      input: resizedIcon,
      top: padding,
      left: padding,
    }])
    .png()
    .toFile(path.join(ICONS_DIR, `icon-maskable-${size}x${size}.png`));

  console.log(`Generated: icon-maskable-${size}x${size}.png`);
}

async function generateSplashScreen({ width, height, name }) {
  const iconSize = Math.floor(Math.min(width, height) / 4);
  const x = Math.floor((width - iconSize) / 2);
  const y = Math.floor((height - iconSize) / 2);

  const resizedIcon = await sharp(SOURCE_ICON)
    .resize(iconSize, iconSize)
    .toBuffer();

  await sharp({
    create: {
      width,
      height,
      channels: 4,
      background: { r: 15, g: 23, b: 42, alpha: 1 },
    },
  })
    .composite([{
      input: resizedIcon,
      top: y,
      left: x,
    }])
    .png()
    .toFile(path.join(SPLASH_DIR, name));

  console.log(`Generated: ${name}`);
}

async function main() {
  if (!fs.existsSync(SOURCE_ICON)) {
    console.error(`Error: Source icon not found at ${SOURCE_ICON}`);
    console.error('Please ensure icon-512x512.png exists in public/icons/');
    process.exit(1);
  }

  fs.mkdirSync(ICONS_DIR, { recursive: true });
  fs.mkdirSync(SPLASH_DIR, { recursive: true });

  console.log('Generating standard icons...');
  for (const size of ICON_SIZES) {
    await generateIcon(size);
  }

  console.log('\nGenerating Apple touch icon...');
  await sharp(SOURCE_ICON)
    .resize(180, 180)
    .png()
    .toFile(path.join(ICONS_DIR, 'apple-touch-icon.png'));
  console.log('Generated: apple-touch-icon.png');

  console.log('\nGenerating maskable icons...');
  for (const size of MASKABLE_SIZES) {
    await generateMaskableIcon(size);
  }

  console.log('\nGenerating shortcut icons...');
  await sharp(SOURCE_ICON).resize(96, 96).png().toFile(path.join(ICONS_DIR, 'shortcut-plan.png'));
  await sharp(SOURCE_ICON).resize(96, 96).png().toFile(path.join(ICONS_DIR, 'shortcut-chat.png'));
  console.log('Generated: shortcut-plan.png, shortcut-chat.png');

  console.log('\nGenerating splash screens...');
  for (const splash of SPLASH_SCREENS) {
    await generateSplashScreen(splash);
  }

  console.log('\n✅ All icons generated successfully!');
}

main().catch(console.error);
