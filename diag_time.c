#include "diag_time.h"

void diag_time (double timesec) {

  int inthrs = lround(timesec) / (60*60);
  int intmin = (lround(timesec) - inthrs*60*60) / 60;
  int intsec = lround(timesec) % 60;
  double timemin = timesec / 60.0;
  double timehrs = timesec / (60.0*60.0);
  char fmt[250];

  FILE *fid = fopen ("diag_time.dat", "w");
  if (fid == NULL) {
    fprintf (stderr, "error: could not write file diag_time.dat\n");
    return;
  }
  strcpy (fmt, "%5.2d:%2.2d:%2.2d %7.2f %9.2f %10.2f");
  strcat (fmt, " %% HH:MM:SS=hours=minutes=seconds\n");
  fprintf (fid, fmt, inthrs,intmin,intsec, timehrs,timemin,timesec);
  fclose (fid);

/* original version (before 06/03/06):
  FILE *file = fopen("diag_time.dat", "w");
  fprintf(file, "Time elapsed:%5.2d:%2.2d:%2.2d =%8d =%15.6f seconds",
          inthrs, intmin, intsec, (int)lrint(timesec), timesec);
*/

/* corresponding Matlab output (as of 06/03/06):
  fid = fopen ('diag_time.dat', 'w');
  fmt1 = '%5.2d:%2.2d:%2.2d %7.2f %9.2f %10.2f';
  fmt2 = ' %% HH:MM:SS=hours=minutes=seconds';
  fmt = [fmt1, fmt2, '\n'];
  fprintf (fid, fmt, inthrs,intmin,intsec, timehrs,timemin,timesec);
  fclose (fid);

% Explanation of the format conversions above:
% I am assuming that the code will not run for more than 7 days.
% To format the time of 7 days in hours, minutes, and seconds,
% we need sufficiently many digits to show
%   7 days = 168 hours = 10080 minutes = 604800 seconds
% Showing each with 2 decimal digits thus requires
%          %6.2f hours = %8.2f minutes =  %9.2f seconds
% But there is sufficient space, so oversupply by 1 everywhere.
% Ordinarily, this will give another space, which will make the
% output easier to read.
*/
}

