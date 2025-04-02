import React from 'react';
import Link from 'next/link';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';

const Navigation: React.FC = () => {
  return (
    <AppBar position="static" sx={{ mb: 4 }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, textAlign: 'right' }}>
          روبوک
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" component={Link} href="/">
            خانه
          </Button>
          <Button color="inherit" component={Link} href="/upload">
            آپلود کتاب
          </Button>
          <Button color="inherit" component={Link} href="/reader">
            خواندن کتاب
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation; 