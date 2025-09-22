# Tell latexmk how to build .asy → .pdf and when to run it.

add_cus_dep( 'asy', 'pdf', 0, 'asy2pdf' );

sub asy2pdf {
  my $src = shift;                # e.g., doc-1.asy
  my $cmd = "asy -f pdf \"$src\"";
  print "Running: $cmd\n";
  return system($cmd);
}

# Ensure latexmk knows these intermediates get cleaned
$clean_ext .= ' %R-*.asy %R-*.pdf %R.pre';
