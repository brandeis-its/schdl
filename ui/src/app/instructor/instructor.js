angular.module('schdl.instructor', ['ngResource'])

.factory('Instructor', ['$resource', function($resource) {
	var Instructor = $resource('/api/instructors/:school/:id');
	return Instructor;
}])

.controller('InstructorCtrl', ['$scope', 'instructor', 'titleService', function($scope, instructor, titleService) {
	$scope.instructor = instructor;
    titleService(instructor.name);
}])

;
