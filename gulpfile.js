const gulp = require('gulp');

// Copy CSS
gulp.task('css', function() {
    return gulp.src('src/css/*.css')
        .pipe(gulp.dest('static/css'));
});

// Copy JS
gulp.task('js', function() {
    return gulp.src('src/js/*.js')
        .pipe(gulp.dest('static/js'));
});

// Copy images
gulp.task('images', function() {
    return gulp.src('src/images/*')
        .pipe(gulp.dest('static/images'));
});

// Default task
gulp.task('default', gulp.series('css', 'js', 'images'));
