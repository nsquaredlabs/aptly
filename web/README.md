# Aptly Website

This directory contains the Aptly website (marketing + documentation) built with Next.js and Nextra.

## Getting Started

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The site will be available at `http://localhost:3000`:
- Marketing homepage: `http://localhost:3000`
- Documentation: `http://localhost:3000/docs`

### Build for Production

```bash
npm run build
```

### Start Production Server

```bash
npm run start
```

## Project Structure

```
web/
├── pages/
│   ├── index.tsx        # Marketing homepage
│   ├── docs/            # Documentation pages (MDX)
│   └── _app.tsx         # Next.js app wrapper with MDXProvider
├── components/          # Custom MDX components
├── public/              # Static assets (logos, favicon)
├── styles/              # Global CSS
├── theme.config.tsx     # Nextra theme configuration
├── next.config.js       # Next.js configuration
└── package.json         # Dependencies
```

## Editing Content

### Marketing Pages

Marketing pages are regular React components in `pages/` directory:
- `pages/index.tsx` - Homepage

To add more marketing pages, create new `.tsx` files at the root of `pages/`:
- `pages/pricing.tsx` → `/pricing`
- `pages/about.tsx` → `/about`

### Documentation Pages

1. All documentation pages are in `pages/docs/` as `.mdx` files
2. Navigation is configured via `_meta.json` files in each directory
3. Custom components are available in `components/` directory

### Available Custom Components

- `<Card>` and `<CardGroup>` - Feature cards
- `<CodeGroup>` - Tabbed code examples
- `<ResponseExample>` - API response examples
- `<Callout>`, `<Note>`, `<Warning>`, `<Info>`, `<Error>`, `<Success>` - Callout boxes
- `<ParamField>` - API parameter documentation
- `<ResponseField>` - API response field documentation
- `<Accordion>` and `<AccordionGroup>` - Collapsible sections
- `<Check>` - Checkmark list items
- `<Tip>` - Tip callouts
- `<Expandable>` - Expandable content

## Deployment

This site is configured to deploy to Vercel with the following settings:

- **Domain**: `aptly.nsquaredlabs.com`
- **Homepage**: `/` (marketing)
- **Documentation**: `/docs`

### Deploy to Vercel

1. **Connect Repository**
   - Go to [Vercel](https://vercel.com)
   - Import your GitHub repository
   - Select the `web` directory as the root directory

2. **Configure Build Settings**
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

3. **Set Environment Variables** (if needed)
   - No environment variables required for static site

4. **Configure Custom Domain**
   - In Vercel dashboard, go to Settings → Domains
   - Add `aptly.nsquaredlabs.com`
   - Update DNS records as instructed by Vercel:
     - A record: `76.76.21.21`
     - Or CNAME: `cname.vercel-dns.com`

5. **Deploy**
   - Push to main branch to trigger automatic deployment
   - Or use `vercel --prod` from CLI

### DNS Configuration

Point your domain to Vercel:
```
Type: A
Name: @
Value: 76.76.21.21

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

### Testing Deployment

After deployment, verify:
- https://aptly.nsquaredlabs.com loads the marketing homepage
- https://aptly.nsquaredlabs.com/docs loads the documentation
- All navigation links work
- Search functionality works (in docs)
- Dark mode toggle works

## Contributing

### Adding Marketing Content

1. Create/edit React components in `pages/` directory
2. Update `pages/_meta.json` if needed for navigation
3. Test locally with `npm run dev`
4. Commit and push to trigger deployment

### Adding Documentation

1. Create/edit MDX files in the `pages/docs/` directory
2. Update `_meta.json` files to add navigation entries
3. Test locally with `npm run dev`
4. Ensure all links work and components render correctly
5. Commit and push to trigger deployment
