angular.module('schdl.course', ['ngResource'])

.factory('Course', ['$resource', function($resource) {
  var Course = $resource('/api/courses/:school/:term/:id');
  return Course;
}])

.directive('schdlSectionStatus', function() {
  return {
    restrict: 'E',
    controller: ['$scope', function($scope) {
      $scope.exists = function(val) {
        return angular.isDefined(val) && val !== null;
      };
    }],
    scope: {
      'status': '=',
      'statusText': '=',
      'enrolled': '=',
      'limit': '=',
      'waiting': '='
    },
    templateUrl: '/static/course/sectionStatus.tpl.html'
  };
})

.controller('CourseCtrl', ['$scope', 'course', 'Schedule', 'titleService', function($scope, course, Schedule, titleService) {
  $scope.course = course;
  titleService(course.code + ': ' + course.name + ' - ' + course.term.name);
}])

;
