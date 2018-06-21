angular.module('schdl.student_interest', ['ngResource'])

.factory('StudentInterest', ['$resource', function($resource) {
  return $resource('/api/student_interest/:school/:term');
}])

.controller('StudentInterestCtrl', ['$scope', 'school', 'StudentInterest', 'titleService', function($scope, school, StudentInterest, titleService) {
  $scope.get = function getStudentInterest(term) {
    $scope.loading = true;
    $scope.data = StudentInterest.query({school: school.fragment, term: term});
    $scope.data.$promise['finally'](function() {
      $scope.loading = false;
    });
  };
  $scope.setOrder = function setOrder(sort) {
    if (angular.equals($scope.sort, sort)) {
      $scope.reverse = !$scope.reverse;
    } else {
      $scope.sort = sort;
      $scope.reverse = false;
    }
  };
  $scope.setOrder(['course_code', 'section']);
  $scope.form = {term: school.defaultTerm};
  $scope.filter = '';
  titleService('Student Interest');
}])

;
