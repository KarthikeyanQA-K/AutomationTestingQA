package Test;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class login {
	 public static void main(String[] args) {
	        

	        // Initialize WebDriver
	        WebDriver driver = new ChromeDriver();

	       
	            // Open the login page
	            driver.get("https://www.google.com");

	            // Maximize the browser window
	            driver.manage().window().maximize();
System.out.println("suuesss");
	    }
	}

