angular.module('schdl.subject', ['ngResource'])

.factory('Subject', ['$resource', function($resource) {
  var Subject = $resource('/api/subjects/:school/:term/:id');
  return Subject;
}])

.controller('SubjectCtrl', ['$scope', 'subject', 'titleService', function($scope, subject, titleService) {
  $scope.subject = subject;
  titleService(subject.name + ' - ' + subject.term.name);
}])

;
