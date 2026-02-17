# Aptly Documentation

This directory contains the Aptly documentation site built with Next.js and Nextra.

## Getting Started

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

The docs will be available at `http://localhost:3000/docs`

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
docs/
├── pages/           # MDX documentation files
├── components/      # Custom MDX components
├── public/          # Static assets (logos, favicon)
├── styles/          # Global CSS
├── theme.config.tsx # Nextra theme configuration
├── next.config.js   # Next.js configuration
└── package.json     # Dependencies
```

## Editing Documentation

1. All documentation pages are in the `pages/` directory as `.mdx` files
2. Navigation is configured via `_meta.json` files in each directory
3. Custom components are available in `components/` directory

### Available Custom Components

- `<Card>` and `<CardGroup>` - Feature cards
- `<CodeGroup>` - Tabbed code examples
- `<ResponseExample>` - API response examples
- `<Callout>` - Note/Warning/Tip callouts

## Deployment

This site is configured to deploy to Vercel with the following settings:

- **Domain**: `aptly.nsquaredlabs.com`
- **Base Path**: `/docs`
- **Root Redirect**: `/` → `/docs`

### Deploy to Vercel

1. **Connect Repository**
   - Go to [Vercel](https://vercel.com)
   - Import your GitHub repository
   - Select the `docs` directory as the root directory

2. **Configure Build Settings**
   - Framework Preset: Next.js
   - Build Command: `npm run build`
   - Output Directory: `.next`
   - Install Command: `npm install`

3. **Set Environment Variables** (if needed)
   - No environment variables required for static docs

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
- https://aptly.nsquaredlabs.com/docs loads the documentation
- https://aptly.nsquaredlabs.com redirects to /docs
- All navigation links work
- Search functionality works
- Dark mode toggle works

## Contributing

When adding new documentation:

1. Create/edit MDX files in the `pages/` directory
2. Update `_meta.json` files to add navigation entries
3. Test locally with `npm run dev`
4. Ensure all links work and components render correctly
5. Commit and push to trigger deployment
