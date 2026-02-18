import nextra from 'nextra'

const withNextra = nextra({
  defaultShowCopyCode: true,
  latex: true,
})

export default withNextra({
  images: {
    unoptimized: true,
  },
})
